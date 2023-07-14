from django.shortcuts import render, redirect
# from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from . models import Profile, Post, LikePost, FollowersCount
from django.db import transaction
from itertools import chain
import random
#Craete your views here.

@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    user_following = FollowersCount.objects.filter(follower=request.user.username)

    user_following_list = [users.user for users in user_following]

    feed_list = Post.objects.filter(user__in=user_following_list)
    
    feed_list_with_user_profile = []
    for user in feed_list:
        image =Profile.objects.get(user= User.objects.get(username=user.user))
        profile_image = image.profile_img
        post_image = user.image
        caption = user.caption

        id = user.id
        like_label = 'No likes' if user.no_of_likes == 0 else f"Liked by  {user.no_of_likes}  persion" if  user.no_of_likes == 1 else f'Liked by  {user.no_of_likes} people'

        user_dic = {'user':user, 'profile_image':profile_image, 'id':id, 'like_label':like_label, 'post_image':post_image, 'caption':caption}
        feed_list_with_user_profile.append(user_dic)



    # user suggestion starts 
    all_users = User.objects.all()
    user_following_all = [User.objects.get(username=user.user) for user in user_following]

    suggestion_list = [x for x in all_users  if (x not in user_following_all) and (x != user_object)]
    random.shuffle(suggestion_list)


    user_details = [user.id for user in suggestion_list]
    user_details_list = [Profile.objects.filter(id_user=ids) for ids in user_details ]
    user_details_list = list(chain(*user_details_list))


    followers_count = [len(FollowersCount.objects.filter(user=x)) for x in user_details_list]

    ######
    # Creating a new list of dictionaries 

    user_details_with_followers_count = []

    for user, count  in zip(user_details_list, followers_count):
        imag = user.profile_img
        label = 'follower' if count <= 1 else 'followers'
        user_dic = {'user':user, "imag":imag, 'count':count, 'label':label}
        user_details_with_followers_count.append(user_dic)

    context = {
        'user_profile': user_profile,
        # 'posts': feed_list ,
        'posts': feed_list_with_user_profile ,
        'user_details_list':user_details_with_followers_count,
    }
    return render(request, 'index.html', context)

@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id=post_id)
    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

    if like_filter == None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes = post.no_of_likes+1
        post.save()
        return redirect('/')
    else:
        like_filter.delete()
        post.no_of_likes = post.no_of_likes-1
        post.save()
        return redirect('/')

@login_required(login_url='signin')
def search(request):
    username = request.user.username
    user_object = User.objects.get(username=username)
    user_profile = Profile.objects.get(user = user_object)

    if request.method == 'POST':
        username = request.POST['username']

        username_object = User.objects.filter(username__icontains=username)
        username_profile = [users.id for users in username_object]
        username_profile_list = list(chain(*[ Profile.objects.filter(id_user=user_id) for user_id in username_profile]))

    context = {
        'user_profile': user_profile,
        'username_profile_list':username_profile_list,
    }

    return render(request, 'search.html', context)

@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        image = request.FILES.get('image', user_profile.profile_img)
        bio = request.POST['bio']
        location = request.POST['location']

        user_profile.profile_img = image
        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()

        return redirect('settings')

    return render(request, 'setting.html', {'user_profile': user_profile})


@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']

        if FollowersCount.objects.filter(follower=follower, user=user).first():
            delete_follower = FollowersCount.objects.get(follower=follower, user=user)
            delete_follower.delete()
        else: 
            new_follower = FollowersCount.objects.create(follower=follower, user=user)
            # new_follower.save()
        return redirect('/profile/'+user)
    else:
        return redirect('/')


@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_post_length = len(user_posts)
   

    user_data = {
        'post_name': 'post' if user_post_length <= 1 else 'posts',
        'button_text': 'Unfollow' if FollowersCount.objects.filter(follower=request.user.username, user=pk).first() else 'Follow',
        'user_followers': len(FollowersCount.objects.filter(user=pk)),
        'user_following': len(FollowersCount.objects.filter(follower=pk)),
        'followers_text': 'follower' if len(FollowersCount.objects.filter(user=pk)) <= 1 else 'followers',
}

    context = {
        'user_object':user_object,
        'user_profile':user_profile,
        'user_posts':user_posts,
        'user_post_length':user_post_length,
        'user_data':user_data,
        
    }

    return render(request, 'profile.html', context)

@login_required(login_url='signin')
def upload(request):

    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']

        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()

        return redirect('/')
    else:
        return redirect('/')

def signup(request):

    if request.method == 'POST':
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        password_conf = request.POST["password2"]

        
        def validate_password(password):
            # Set of valid characters
            valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@,.")

            # Minimum length requirement
            min_length = 8

            # Data structure to keep track of character counts
            char_counts = {}

            # Check if password meets minimum length requirement
            if len(password) < min_length:
                messages.info(request,  'Should be between 8 to 15 characters long')
                return False

            # Iterate over characters in password
            for char in password:
                # Check if character is valid
                if char not in valid_chars:
                    messages.info(request,  'invalid character')
                    return False

                # Update character count
                if char in char_counts:
                    char_counts[char] += 1
                else:
                    char_counts[char] = 1

            # Check if password contains at least one uppercase, one lowercase, and one digit
            has_upper = False
            has_lower = False
            has_digit = False
            for char, count in char_counts.items():
                if char.isupper():
                    has_upper = True
                elif char.islower():
                    has_lower = True
                elif char.isdigit():
                    has_digit = True

            if has_upper == False:
                messages.info(request,  'Should have at least one uppercase characters')
            elif has_lower == False:
                messages.info(request,  'Should have at least one lowercase characters')
            elif has_digit == False:
                messages.info(request,  'Should have at least one digit')

            return has_upper and has_lower and has_digit
        
        # validate_password(password)
    
        if(validate_password(password)):

            if password == password_conf:
                if User.objects.filter(email=email).exists():
                    messages.info(request, 'Email Taken')
                    return redirect('signup')
                elif User.objects.filter(username=username).exists():
                    messages.info(request, 'Username Taken')
                    return redirect('signup')
                else:
                    
                    with transaction.atomic():
                        user = User.objects.create_user(username=username, email=email, password=password)
                        new_profile = Profile.objects.create(user=user, id_user=user.id)

                    return redirect('index')
            else:
                messages.info(request, 'Password Not Matching')
                return redirect('signup')
        else:
            # return render(request, 'signup.html')
            return redirect('signup')

    else:
        return render(request, 'signup.html')

def signin(request):

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)
        if user:
            auth.login(request, user)
            return redirect('index')
        else:
            messages.info(request, 'User Invalid')
            return redirect('signin')

    else:
        return render(request, 'signin.html')

@login_required(login_url='signin')    
def logout(request):
    auth.logout(request)
    return redirect('signin')











