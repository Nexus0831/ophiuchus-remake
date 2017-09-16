from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class CustomUser(AbstractUser):
    introduction = models.TextField(verbose_name='自己紹介', null=True)
    gitHub_url = models.CharField(max_length=512, verbose_name="GitHub_URL")


#プロジェクト
class Project(models.Model):
    leader = models.ForeignKey(CustomUser, default='', related_name='leader')
    sub_leader = models.ForeignKey(CustomUser, default='', null=True, related_name='sub_leader')
    project_name = models.CharField(max_length=30, verbose_name='プロジェクト名')
    over_view = models.TextField(verbose_name='概要')
    start_date = models.DateField(verbose_name='開始日')
    completed_date = models.DateField(verbose_name='完了予定日時')
    repository_id = models.IntegerField(default="", verbose_name='リポジトリID')
    repository_name = models.CharField(max_length=512, default="", verbose_name='リポジトリ名')
    repository_url = models.CharField(max_length=512, default="", verbose_name='リポジトリURL')
    is_completed = models.BooleanField(default=False, verbose_name='完了')

    def __str__(self):
        return self.project_name


#プロセス
class Process(models.Model):
    parent = models.ForeignKey(Project)
    process_number = models.IntegerField(default=1, verbose_name='プロセス番号')
    process_name = models.CharField(max_length=30, verbose_name='プロセス名')
    process_contents = models.TextField(verbose_name='プロセス内容')
    process_start = models.DateField(verbose_name='開始日')
    process_completed = models.DateField(verbose_name='完了予定日時')
    completed_process = models.BooleanField(default=False, verbose_name='完了')

    def __str__(self):
        return self.process_name


#アサイン
class Assign(models.Model):
    project = models.ForeignKey(Project, default='', related_name='project')
    user = models.ForeignKey(CustomUser, default='', related_name='user')


#プロセスアサイン
class ProcessAssign(models.Model):
    process = models.ForeignKey(Process, default='', related_name='process')
    person = models.ForeignKey(CustomUser, default='', related_name='person')


#メッセージ
class Message(models.Model):
    send_user = models.ForeignKey(CustomUser, default='', related_name='send_user')
    reception_user = models.ForeignKey(CustomUser, default='', related_name='reception_user')
    title = models.CharField(max_length=50, verbose_name='タイトル')
    text = models.TextField(verbose_name='本文')
    project = models.ForeignKey(Project, default='', related_name='application_project')

    def __str__(self):
        return self.title


#招待
class Invitation(models.Model):
    send_user = models.ForeignKey(CustomUser, default='', related_name='invitation_send_user')
    reception_user = models.ForeignKey(CustomUser, default='', related_name='invitation_user')
    project = models.ForeignKey(Project, related_name='invitation_project')
    title = models.CharField(max_length=50, verbose_name='タイトル')
    text = models.TextField(verbose_name='本文')

    def __str__(self):
        return self.title


# 募集
class Recruitment(models.Model):
    recruiter = models.ForeignKey(CustomUser, default='', related_name='recruiter')
    project = models.ForeignKey(Project, default='', related_name='rec_project')
    title = models.CharField(max_length=50, verbose_name='タイトル')
    text = models.TextField(verbose_name='本文')
    requirement = models.TextField(verbose_name='参加条件')

    def __str__(self):
        return self.title


#履歴
class History(models.Model):
    project = models.ForeignKey(Project, default='')
    date = models.DateTimeField(auto_now=True, verbose_name='履歴日')
    history = models.CharField(max_length=255)
