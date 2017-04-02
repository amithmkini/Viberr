from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .forms import AlbumForm, SongForm, UserForm
from .models import Album, Song
from numpy import genfromtxt, savetxt
import numpy as np
import hashlib

AUDIO_FILE_TYPES = ['wav', 'mp3', 'ogg']
IMAGE_FILE_TYPES = ['png', 'jpg', 'jpeg']


def create_album(request):
    if not request.user.is_authenticated():
        return render(request, 'music/login.html')
    else:
        form = AlbumForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            album = form.save(commit=False)
            album.user = request.user
            album.album_logo = request.FILES['album_logo']
            file_type = album.album_logo.url.split('.')[-1]
            file_type = file_type.lower()
            if file_type not in IMAGE_FILE_TYPES:
                context = {
                    'album': album,
                    'form': form,
                    'error_message': 'Image file must be PNG, JPG, or JPEG',
                }
                return render(request, 'music/create_album.html', context)
            album.save()
            return render(request, 'music/detail.html', {'album': album})
        context = {
            "form": form,
        }
        return render(request, 'music/create_album.html', context)


def create_song(request, album_id):
    form = SongForm(request.POST or None, request.FILES or None)
    album = get_object_or_404(Album, pk=album_id)
    if form.is_valid():
        albums_songs = album.song_set.all()
        for s in albums_songs:
            if s.song_title == form.cleaned_data.get("song_title"):
                context = {
                    'album': album,
                    'form': form,
                    'error_message': 'You already added that song',
                }
                return render(request, 'music/create_song.html', context)
        song = form.save(commit=False)
        song.album = album
        song.audio_file = request.FILES['audio_file']
        file_type = song.audio_file.url.split('.')[-1]
        file_type = file_type.lower()
        if file_type not in AUDIO_FILE_TYPES:
            context = {
                'album': album,
                'form': form,
                'error_message': 'Audio file must be WAV, MP3, or OGG',
            }
            return render(request, 'music/create_song.html', context)

        song.save()
        return render(request, 'music/detail.html', {'album': album})
    context = {
        'album': album,
        'form': form,
    }
    return render(request, 'music/create_song.html', context)


def delete_album(request, album_id):
    album = Album.objects.get(pk=album_id)
    album.delete()
    albums = Album.objects.all()
    return render(request, 'music/index.html', {'albums': albums})


def delete_song(request, album_id, song_id):
    album = get_object_or_404(Album, pk=album_id)
    song = Song.objects.get(pk=song_id)
    song.delete()
    return render(request, 'music/detail.html', {'album': album})


def detail(request, album_id):
    if not request.user.is_authenticated():
        return render(request, 'music/login.html')
    else:
        user = request.user
        album = get_object_or_404(Album, pk=album_id)
        return render(request, 'music/detail.html', {'album': album, 'user': user})


def favorite(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    try:
        if song.is_favorite:
            song.is_favorite = False
        else:
            song.is_favorite = True
        song.save()
    except (KeyError, Song.DoesNotExist):
        return JsonResponse({'success': False})
    else:
        return JsonResponse({'success': True})

def counter(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    encrypted_id = song.encrypted_id
    data_matrix = genfromtxt('music/matrix.csv',delimiter=",")
    f = open('music/dictionary_user.txt','r')
    username = request.user.username
    print(username)
    m = hashlib.sha1(username.encode('utf-8')).hexdigest()
    print(m)
    for line in f:
        data = line.split('\t')
        if data[0] == m:
            user_id = data[1]
            break
    print(user_id)
    f.close()

    f2 = open('music/dictionary_song.txt','r')
    for line in f2:
        data = line.split('\t')
        if data[0] == encrypted_id:
            song_id = data[1]
            break

    print(user_id,song_id)
    data_matrix[int(user_id)][int(song_id)] +=  1
    np.savetxt("music/matrix.csv",data_matrix,delimiter=",")
    print(data_matrix[int(user_id)][3])

    return render(request, 'music/success.html')

def favorite_album(request, album_id):
    album = get_object_or_404(Album, pk=album_id)
    try:
        if album.is_favorite:
            album.is_favorite = False
        else:
            album.is_favorite = True
        album.save()
    except (KeyError, Album.DoesNotExist):
        return JsonResponse({'success': False})
    else:
        return JsonResponse({'success': True})


def index(request):
    if not request.user.is_authenticated():
        return render(request, 'music/login.html')
    else:
        albums = Album.objects.all()
        song_results = Song.objects.all()
        query = request.GET.get("q")
        if query:
            albums = albums.filter(
                Q(album_title__icontains=query) |
                Q(artist__icontains=query)
            ).distinct()
            song_results = song_results.filter(
                Q(song_title__icontains=query)
            ).distinct()
            return render(request, 'music/index.html', {
                'albums': albums,
                'songs': song_results,
            })
        else:
            return render(request, 'music/index.html', {'albums': albums})


def logout_user(request):
    logout(request)
    form = UserForm(request.POST or None)
    context = {
        "form": form,
    }
    return render(request, 'music/login.html', context)


def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                albums = Album.objects.all()
                return render(request, 'music/index.html', {'albums': albums})
            else:
                return render(request, 'music/login.html', {'error_message': 'Your account has been disabled'})
        else:
            return render(request, 'music/login.html', {'error_message': 'Invalid login'})
    return render(request, 'music/login.html')


def register(request):
    form = UserForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user.set_password(password)
        user.save()
        user = authenticate(username=username, password=password)


        data_matrix = genfromtxt('music/matrix.csv',delimiter=",")
        f = open('music/dictionary_user.txt','a')
        m = hashlib.sha1(username.encode('utf-8')).hexdigest()
        print(m)
        new_row = [0] * data_matrix.shape[1]
        num_users = data_matrix.shape[0]
        data_matrix = np.vstack([data_matrix, new_row])
        savetxt("music/matrix.csv",data_matrix,delimiter=",")
        f.writelines(m+'\t'+str(num_users)+'\n')
        f.close()
        # print(request.user.username)
        # print(user_list)

        if user is not None:
            if user.is_active:
                login(request, user)
                albums = Album.objects.all()
                return render(request, 'music/index.html', {'albums': albums})
    context = {
        "form": form,
    }
    return render(request, 'music/register.html', context)

def songs(request, filter_by):
    if not request.user.is_authenticated():
        return render(request, 'music/login.html')
    else:
        try:
            song_ids = []
            for album in Album.objects.all():
                for song in album.song_set.all():
                    song_ids.append(song.pk)
            users_songs = Song.objects.filter(pk__in=song_ids)
            if filter_by == 'favorites':
                users_songs = users_songs.filter(is_favorite=True)
        except Album.DoesNotExist:
            users_songs = []
        return render(request, 'music/songs.html', {
            'song_list': users_songs,
            'filter_by': filter_by,
        })

# Recommender

def similarity(u,v):
    # print "Calculating sim between " + str(u) + " and " + str(v),
    numerator = float(np.inner(u,v))
    norm_u = np.linalg.norm(u)
    norm_v = np.linalg.norm(v)
    denominator = norm_u * norm_v
    # print numerator, denominator
    # print " = " + str(numerator/denominator)
    return numerator/denominator

def score(user_index,song_index,data):
    u = data[user_index]
    u_avg = np.mean(u)
    numerator = 0
    denominator = 0
    # print 'similarity = '
    for u1 in data:
        u1_avg = np.mean(u1)
        sim = similarity(u,u1)
        # print sim,
        numerator += sim * (u[song_index]-u1_avg)
        denominator += abs(sim)
    return u_avg + (numerator/denominator)

def prediction(user_index,data,k=16):
    score_list = []
    print("Constructing score list...",)
    for i in range(data.shape[1]):
        s = score(user_index, i, data)
        score_list.append((s, i))
    score_list.sort()
    print("Done")
    recommendations = score_list[data.shape[1]-k:data.shape[1]]
    rec_songs = [y for (x,y) in recommendations]
    # print score_list
    print(rec_songs)
    return rec_songs

def normalizeMatrix(data_matrix):

    num_rows = data_matrix.shape[0]
    num__cols = data_matrix.shape[1]

    data_matrix_normalized = [[0]*num__cols] * num_rows

    #normalizing the data
    for i in range(num_rows):
        data_matrix_normalized[i] = data_matrix[i] / float(np.amax(data_matrix[i]))

    return np.asarray(data_matrix_normalized)




def recommended(request):

    f = open('music/dictionary_user.txt','r')
    username = request.user.username
    print(username)
    m = hashlib.sha1(username.encode('utf-8')).hexdigest()
    print(m)
    for line in f:
        data = line.split('\t')
        if data[0] == m:
            user_id = int(data[1])
            break
    print(user_id)
    f.close()

    if not request.user.is_authenticated():
        return render(request, 'music/login.html')
    else:
        try:
            song_ids = []
            # The recommended songs should come out here.
            print('We reached here')
            data = genfromtxt("music/matrix.csv",delimiter=",")
            num_users = data.shape[0]
            data_normal = normalizeMatrix(data)
            u = user_id
            final_list = prediction(u,data_normal)
            print(final_list)
            encrypted_list = []
            f = open('music/dictionary_song.txt','r')
            for line in f:
                data = line.split('\t')
                for x in final_list:
                    if x == int(data[1]):
                        encrypted_list.append(data[0])

            for album in Album.objects.all():
                for song in album.song_set.all():
                    for x in encrypted_list:
                        if x == song.encrypted_id:
                            song_ids.append(song.pk)

            users_songs = Song.objects.filter(pk__in=song_ids)
        except Album.DoesNotExist:
            users_songs = []
        return render(request, 'music/recommended.html', {
            'song_list': users_songs
        })
