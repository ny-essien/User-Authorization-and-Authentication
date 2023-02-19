import random
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.core.mail import send_mail, EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from Authorize import settings
from .tokens import generate_token

# Create your views here.
def home(request):
    return render(request, 'authorization/home.html')


def searchUser(request):

    q = request.GET.get('q') if request.GET.get('q') != None else ""

    users = User.objects.filter(Q(username__icontains = q)|
                                Q(first_name__icontains = q)|
                                Q(last_name__icontains = q))

    return render(request, "authorization/home.html", {'users':users})


def registrationPage(request):

    if request.method == "POST":
        username = request.POST['username']
        first_name = request.POST['fname']
        last_name = request.POST['lname']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if User.objects.filter(username__icontains = username):
            messages.error(request, 'Username already exist')
            return redirect('register')

        if User.objects.filter(email__icontains = email):
            messages.error(request, 'email already exist')
            return redirect('register')

        if len(username) > 20:
            messages.error(request, 'too many characters, username should not be more than 20 charaters')
            return redirect('register')

        if password1 != password2:
            messages.error(request, 'Password Mismatch')
            return redirect('register')

        if not username.isalnum():
            messages.error(request, 'username must be alphae-numeric')
            return redirect('register')

        if len(password1) < 8:
            messages.error(request, 'password should be more than 8 characters')
            return redirect('register')

        
        user = User.objects.create_user(username, email, password1)
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = False
        user.save()

        #Welcome Email
        subject = 'Welcome to CryptChain!!!'
        message = 'Account sucessfully created\nThank you for signing up with us\n\nWe have sent you a confirmation email, please confirm your email to activate account'
        from_mail = settings.EMAIL_HOST_USER
        to_list = [user.email]

        #send mail
        send_mail(subject, message, from_mail, to_list, fail_silently=True)

        #Confirmation Email
        current_site = get_current_site(request)
        email_subject = 'Activate Account at CryptChain PLC!!!'
        message2 = render_to_string('authorization/email_confirmation.html', {

            'name':user.first_name,
            'domain': current_site,
            'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
            'token' : generate_token.make_token(user)
        })

        email = EmailMessage(

            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [user.email]
        )

        email.fail_silently = True
        email.send()

        messages.success(request, 'Account successfully created. We have sent a link to your email, please confirm email to activate account')
        return redirect('signin')

    return render(request, 'authorization/registration.html')

def activate_account(request, uid64, token):

    try:

        uid = force_text(urlsafe_base64_decode(uid64))
        user = User.objects.get( pk = uid)

    except(TypeError, ValueError, OverflowError, User.DoesNotExist):

        user = None

    if user is not None and generate_token.check_token(user,token):

        user.is_active = True
        user.save()
        login(request, user)
        return redirect('home')

    
    else:

        return render(request, 'authorization/activate.html')

def loginPage(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username = username, password = password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully')
            return redirect('home')

        else:
            messages.error(request, 'Incorrect username or password')

    return render(request, 'authorization/login.html', {'msg':'Login',})

def userList(request):
    users = User.objects.all()
    return render(request, 'authorization/users.html', {'users':users})


def updateProfile(request, pk):

    page = 'update'

    user = User.objects.get(pk = pk)

    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    email = user.email

    if request.method == "POST":
        user.username = request.POST['username'].lower()
        user.first_name = request.POST['fname']
        user.last_name = request.POST['lname']
        user.email = request.POST['email']
        user.save()
        messages.success(request,"Updated successfully")
        return redirect('home')

    
    context = {

        'username':username,
        'first_name':first_name,
        'last_name':last_name,
        'email': email,
        'page':page

    }
    return render(request, "authorization/registration.html", context)


def viewProfile(request):

    user = User.objects.get(pk = request.user.id)
    return render(request, "authorization/profile.html", {'user':user})
    #return HttpResponse(user.id)


def deleteUser(request, pk):

    user = User.objects.get(pk = pk)  
    users = User.objects.all()
    ids = []
    for uu in users:
        ids.append(uu.id)

    max_id = max(ids)

    if not request.user.is_superuser:
        return HttpResponse('Permission denied you have to be an admin to delete a user')

   

    if request.method =="POST":

        if user.is_superuser:
            user.delete()
            while True:
                userid = random.randint(1,max_id + 1)
                try:
                    superuser = User.objects.get(pk = userid)
                    superuser.is_superuser = True
                    superuser.is_staff = True
                    messages.success(request,'User deleted successfully')
                    superuser.save()
                    return redirect('users-list')

                except:
                    continue

        elif user.is_superuser == False:
            
            user.delete()
            messages.success(request, "User deleted successfully")       
            return redirect('users-list')

    return render(request, "authorization/delete.html", {'obj':user})

def changePassword(request):

    user = User.objects.get(pk = request.user.id)

    if request.method == "POST":

        old_password = request.POST['old']
        new_password = request.POST['new1']
        new_password2 = request.POST['new2']

        if not user.check_password(old_password):
            messages.error(request, 'Wrong Password')
            return redirect('change-password')

        if len(new_password) < 8:
            messages.error(request, 'Password must be 8 characters or more ')
            return redirect('change-password')

        if new_password != new_password2:
            messages.error(request, 'Password Mismatch')
            return redirect('change-password')

        #user.password.delete()
        user.set_password(new_password)
        user.save()
        login(request,user)
        return redirect('profile')

    return render(request, "authorization/changepassword.html")

def logoutRequest(request):

    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('home')
