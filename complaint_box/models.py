from django.db import models


class register(models.Model):
    userphoto = models.CharField(max_length=200)
    useremail = models.CharField(max_length=200)
    username = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)
    password = models.CharField(max_length=200)

class complaint(models.Model):
    COMPLAINTTO = (('Trainer','Trainer'),('HR','HR'),('Operations Head','Operations Head'))
    userid = models.IntegerField()
    complaintto = models.CharField(max_length=100,choices= COMPLAINTTO)
    date =models.DateField(max_length=200)
    name =models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    complaintmesg = models.CharField(max_length=200)
    status = models.CharField(max_length=200)

class acknowledgement(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField(max_length=200)
    email = models.CharField(max_length=200)
    ackmesg = models.CharField(max_length=200)

class faculty(models.Model):
    designation = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    useremail = models.CharField(max_length=200)
    password = models.CharField(max_length=200)

class facack(models.Model):
    date = models.DateField(max_length=200)
    designation = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    ackmesg = models.CharField(max_length=200)
    

