from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from .models import *



def first(request):
    return render(request, 'index.html')


def index(request):
    return render(request, 'index.html')


def login(request):
    return render(request, 'login.html')


def registeri(request):
    return render(request, 'registration.html')


def userregistration(request):
    if request.method == "POST":
        userphoto = request.FILES['userphoto']
        fs = FileSystemStorage()
        filename = fs.save(userphoto.name, userphoto)
        useremail = request.POST.get('useremail')
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        reg1 = register(userphoto=userphoto, useremail=useremail, username=username,phone=phone, password=password)
        reg1.save()
        return redirect(login)
    return render(request, 'registration.html')


def complaint1(request):
    return render(request, 'complaintform.html')

def loginuser(request):
    useremail = request.POST.get('useremail')
    password = request.POST.get('password')
    designation = request.POST.get('designation')
    if useremail == 'admin@gmail.com' and password == 'admin':
        request.session['logintdetail'] = useremail
        request.session['admin'] = 'admin'
        return render(request, 'index.html')
    elif faculty.objects.filter(useremail=useremail, password=password, designation = designation).exists():
        facultydetails = faculty.objects.get(useremail=request.POST['useremail'], password=password,designation=designation)
        if facultydetails.password == request.POST['password']:
            request.session['fid'] = facultydetails.id
            request.session['useremail'] = facultydetails.useremail
            request.session['designation'] = facultydetails.designation
            return render(request, 'index.html')
    elif register.objects.filter(useremail=useremail, password=password).exists():
        userdetails = register.objects.get(useremail=request.POST['useremail'], password=password)
        if userdetails.password == request.POST['password']:
            request.session['uid'] = userdetails.id
            request.session['useremail'] = userdetails.useremail
            return render(request, 'index.html')

    else:
        return render(request, 'login.html', {'status': 'Invalid Username or Password'})
    
def logout(request):
    session_keys = list(request.session.keys())
    for key in session_keys:
        del request.session[key]
    return redirect(index)

def profileuser(request):
    return render(request, 'userprofile.html')

def viewprofileuser(request):
    tem = request.session['uid']
    vpro = register.objects.get(id=tem)
    return render(request, 'userprofile.html', {'res': vpro})

# update

def update(request, id):
    upt = register.objects.get(id=id)
    return render(request, 'edituserprofile.html', {'res': upt})

# views for update button

def updates(request, id):
    if request.method == "POST":
        userphoto = request.POST.get('userphoto')
        username = request.POST.get('username')
        useremail = request.POST.get('useremail')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        reg = register(userphoto=userphoto, username=username, useremail=useremail,
                       password=password, phone=phone,id=id)
        reg.save()
        return redirect(viewprofileuser)

def adminviewprofile(request):
    return render(request, 'adminprofile.html')

def trainerviewprofile(request):
    tem = request.session['fid']
    vpro = faculty.objects.get(id=tem)
    return render(request, 'trainerprofile.html', {'res': vpro})


def sendcompaint(request):
    b = request.session['uid']
    if request.method == "POST":
        complaintto = request.POST.get('complaintto')
        date = request.POST.get('date')
        name = request.POST.get('name')
        email = request.POST.get('email')
        complaintmesg = request.POST.get('complaintmesg')
        status = request.POST.get('status')
        reg1 = complaint(complaintto=complaintto,date=date, name=name,email=email, complaintmesg=complaintmesg,status=status,userid=b)
        reg1.save()
        return redirect(complaint1)
    return render(request, 'complaintform.html')

def complaintview(request):
    reg3 = complaint.objects.all()
    return render(request, 'viewcomplaintadmin.html', {'res1': reg3})


def complaintviewall(request):
        if request.session['designation']=='Trainer':
            reg1 = complaint.objects.filter(complaintto = 'Trainer')
            return render(request, 'viewcomplaintall.html', {'res': reg1})
        elif request.session['designation']== 'HR':
            reg3 = complaint.objects.filter(complaintto = 'HR')
            return render(request, 'viewcomplaintall.html', {'res': reg3})
        elif request.session['designation']== 'Operations Head':
            reg5 = complaint.objects.filter(complaintto = 'Operations Head')
            return render(request, 'viewcomplaintall.html', {'res':reg5})
        else:
            return redirect(index)
    

def sendack(request):
    if request.method == "POST":
        if request.session['designation']=='Trainer':
            name = request.POST.get('name')
            date = request.POST.get('date')
            email = request.POST.get('email')
            ackmesg = request.POST.get('ackmesg')
            reg1 = acknowledgement(name=name,date=date,email=email, ackmesg=ackmesg)
            reg1.save()
        elif request.session['designation']== 'HR':
            name = request.POST.get('name')
            date = request.POST.get('date')
            email = request.POST.get('email')
            ackmesg = request.POST.get('ackmesg')
            reg1 = acknowledgement(name=name,date=date,email=email, ackmesg=ackmesg)
            reg1.save()
        elif request.session['designation']== 'Operations Head':
            name = request.POST.get('name')
            date = request.POST.get('date')
            email = request.POST.get('email')
            ackmesg = request.POST.get('ackmesg')
            reg1 = acknowledgement(name=name,date=date,email=email, ackmesg=ackmesg)
            reg1.save()
        else:
            return redirect(index)
    return render(request, 'acknowledgementall.html')

def ackview(request):
    tem = request.session.get('useremail')
    reg3 = acknowledgement.objects.filter(email = tem)
    return render(request, 'viewacknowledgement.html', {'res1': reg3})     
        
# views for update button
def registerview(request):
    reg=register.objects.all()
    return render(request,'viewregister.html',{'res':reg})

def admindelete(request, id):
    member = register.objects.get(id=id)
    member.delete()
    return redirect(registerview)

def addfaculty(request):
    if request.method=='POST':
        designation = request.POST.get('designation')
        name = request.POST.get('name')
        useremail = request.POST.get('useremail')
        password = request.POST.get('password')
        fac = faculty(designation=designation,name=name,useremail=useremail,password=password)
        fac.save()
    return render(request, 'adduser.html')
        
def facultyview(request):
    fac = faculty.objects.all()
    return render(request, 'viewfaculty.html', {'res1': fac})

def updatestatus(request,id):
       upt1 = complaint.objects.get(id=id)
       return render(request, 'editcomplaint.html', {'res': upt1})
   

def statusupdate(request,id):
    if request.method == "POST":
        complaintto = request.POST.get('complaintto')
        date = request.POST.get('date')
        name = request.POST.get('name')
        email = request.POST.get('email')
        complaintmesg = request.POST.get('complaintmesg')
        status = request.POST.get('status')
        reg1 = complaint(complaintto=complaintto,date=date, name=name,email=email, complaintmesg=complaintmesg,status=status,userid=id,id=id)
        reg1.save()
    return redirect(complaintviewall)

def facultydelete(request, id):
    member = faculty.objects.get(id=id)
    member.delete()
    return redirect(facultyview)

def ackadmin(request):
    if request.method == "POST":
        designation = request.POST.get('designation')
        date = request.POST.get('date')
        name = request.POST.get('name')
        email = request.POST.get('email')
        ackmesg = request.POST.get('ackmesg')
        reg1 = facack(designation=designation,date=date, name=name,email=email,ackmesg=ackmesg)
        reg1.save()
    return render(request, 'adminack.html')

def ackadminviewall(request):
    if request.session['designation']=='Trainer':
        reg1 = facack.objects.filter(designation = 'Trainer')
        return render(request, 'ackadminview.html', {'res': reg1})
    elif request.session['designation']== 'HR':
        reg3 = facack.objects.filter(designation = 'HR')
        return render(request, 'ackadminview.html', {'res': reg3})
    elif request.session['designation']== 'Operations Head':
        reg5 = facack.objects.filter(designation = 'Operations Head')
        return render(request, 'ackadminview.html', {'res':reg5})
    else:
        return redirect(index)
    



              
    



   



