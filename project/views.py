from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import *
from .form import ErrorForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from github import Github
import datetime
from datetime import datetime as nowtime

# Create your views here.
# TODO: トークンを使用してGitHubAPIにアクセス

# --------------------ここから処理簡略化のメソッド-----------------------------------


action = ''


# プロジェクトに参加してるユーザーをリストで返す
def assign_user(project):
    users = []
    assigns = Assign.objects.filter(project=project).values('user')

    for assign in assigns:
        users.append(CustomUser.objects.get(pk=assign['user']))

    return users


# プロセスの担当表をリストで返す
def _assign_process(processes):
    persons = []

    for process in processes:
        assigns = ProcessAssign.objects.filter(process=process)

        for assign in assigns:
            persons.append(ProcessAssign.objects.get(pk=assign.pk))

    return persons


# プロセス削除処理
def _process_deleted(pk):
    process = get_object_or_404(Process, pk=pk)
    persons = ProcessAssign.objects.filter(process=process)
    project = process.parent

    history = History(project=project, history='プロセス：' + process.process_name + 'を削除しました')
    history.save()

    for person in persons:
        person.delete()

    process.delete()


def _get_page(request, list_, page_no, count=10):
    paginator = Paginator(list_, count)

    page = 1

    if request.is_ajax():
        query = page_no
        if query is not None:
            page = query

    try:
        page = paginator.page(page_no)
    except (EmptyPage, PageNotAnInteger):
        page = paginator.page(1)
    return page


def _get_gitHub(user):
    social = user.social_auth.get(provider='github')
    access_token = social.extra_data['access_token']

    gh = Github(access_token)

    return gh


class _Repository:
    name = ''
    url = ''
    star = 0
    update = ''

    def __init__(self, name, url, star, update):
        self.name = name
        self.url = url
        self.star = star
        self.update = update + datetime.timedelta(hours=9)


class _Repository_Id:
    name = ''
    id = 0

    def __init__(self, name, id):
        self.name = name
        self.id = id


class _Watched:
    name = ''
    url = ''

    def __init__(self, name, url):
        self.name = name
        self.url = url


class _Issue:
    title = ''
    url = ''

    def __init__(self, title, url):
        self.title = title
        self.url = url


# --------------------ここまで処理簡略化のメソッド-----------------------------------

# --------------------ここからview関数-----------------------------------


# プロジェクト一覧を表示
@login_required
def project_list(request):
    assigns = Assign.objects.filter(user=request.user).values('project')
    projects = []
    before_projects = []
    progress_projects = []
    after_projects = []
    completed_project = []
    global action

    for assign in assigns:
        projects.append(Project.objects.get(pk=assign['project']))

    date_time = nowtime.now()

    date = datetime.date(date_time.year, date_time.month, date_time.day)

    for pro in projects:
        if pro.is_completed:
            completed_project.append(pro)

        elif date < pro.start_date:
            before_projects.append(pro)

        elif date > pro.completed_date:
            after_projects.append(pro)

        else:
            progress_projects.append(pro)

    invitations = Invitation.objects.filter(reception_user=request.user)

    gh = _get_gitHub(request.user)
    repositories = []

    for repo in gh.get_user().get_repos():
        repositories.append(_Repository_Id(repo.name, repo.id))

    if request.method == "POST":
        error = ErrorForm(request.POST)

        if request.POST['start_date'] > request.POST['completed_date']:
            error.add_error(None, '')

        else:
            project = Project(leader=request.user, project_name=request.POST['name'],
                              over_view=request.POST['over_view'], start_date=request.POST['start_date'],
                              completed_date=request.POST['completed_date'],
                              repository_id=request.POST['repository_id'])

            repository = gh.get_repo(int(request.POST['repository_id']))

            project.repository_name = repository.name
            project.repository_url = repository.html_url

            project.save()

            assign = Assign(project=project, user=request.user)
            assign.save()

            history = History(project=project, history='プロジェクトを作成しました')
            history.save()

            action = 'project_create'

            return redirect('project_list')

    else:
        error = ErrorForm()

    message = action
    action = ''

    return render(request, 'project_list.html', {'before_projects': before_projects, 'invitations': invitations,
                                                         'progress_project': progress_projects,
                                                         'completed_project': completed_project,
                                                         'after_project': after_projects,
                                                         'error': error, 'repositories': repositories,
                                                                   'toast': message})


# プロジェクト詳細
@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    gh = _get_gitHub(request.user)
    global action

    if request.method == 'POST':
        if 'process-add' in request.POST:
            process = Process(parent=project, process_number=request.POST['number'],
                              process_name=request.POST['process_name'],
                              process_contents=request.POST['process_contents'],
                              process_start=request.POST['process_start'],
                              process_completed=request.POST['process_completed'])

            process.save()

            history = History(project=project, history='プロセス：' + process.process_name + 'を作成しました')
            history.save()

            for person in request.POST.getlist('person'):
                user = CustomUser.objects.get(username=person)
                process_assign = ProcessAssign(process=process, person=user)
                process_assign.save()

            action = 'process_add'

            return redirect('project_detail', pk=pk)

        if 'process-edit' in request.POST:
            process = get_object_or_404(Process, pk=request.POST['pk'])

            process.process_number = request.POST['number']
            process.process_name = request.POST['process_name']
            process.process_contents = request.POST['process_contents']
            process.process_start = request.POST['process_start']
            process.process_completed = request.POST['process_completed']

            process.save()

            persons = ProcessAssign.objects.filter(process=process)

            if len(request.POST.getlist('person')) > 0:
                for person in persons:
                    person.delete()

                for person in request.POST.getlist('person'):
                    user = CustomUser.objects.get(username=person)
                    process_assign = ProcessAssign(process=process, person=user)
                    process_assign.save()

            action = 'process_edit'

            history = History(project=project, history='プロセス：' + process.process_name + 'を編集しました')
            history.save()

            return redirect('project_detail', pk=pk)

        if 'project-edit' in request.POST:
            project.project_name = request.POST['name']
            project.over_view = request.POST['over_view']
            project.start_date = request.POST['start_date']
            project.completed_date = request.POST['completed_date']

            repository = gh.get_repo(int(request.POST['repository_id']))

            project.repository_name = repository.name
            project.repository_url = repository.html_url

            project.save()

            history = History(project=project, history='プロジェクトを編集しました')
            history.save()

            action = 'project_edit'

            return redirect('project_detail', pk=pk)

        if 'invitation' in request.POST:
            for reception in request.POST.getlist('reception_user'):
                invitation = Invitation(project=project, send_user=request.user,
                                        reception_user=CustomUser.objects.get(username=reception),
                                        title=request.POST['title'], text=request.POST['text'])

                invitation.save()

                history = History(project=project, history=str(reception) + 'に招待メッセージを送りました')
                history.save()

            action = 'invitation'

            return redirect('project_detail', pk=pk)

        if 'recruitment' in request.POST:
            recruitment = Recruitment(recruiter=request.user, project=project, title=request.POST['title'],
                                      text=request.POST['text'], requirement=request.POST['requirement'])

            recruitment.save()

            history = History(project=project, history='メンバーを募集しました')
            history.save()

            action = 'recruitment'

            return redirect('project_detail', pk=pk)

    is_member = False

    member = assign_user(project)
    name = []

    for user in member:
        name.append(user.username)
        if user == request.user:
            is_member = True

    if is_member:
        processes = Process.objects.filter(parent=project).order_by('process_number')
        users = CustomUser.objects.exclude(username__in=name)

        before = []
        progress = []
        after = []
        completed = []

        date_time = nowtime.now()
        date = datetime.date(date_time.year, date_time.month, date_time.day)

        for pro in processes:
            if pro.completed_process:
                completed.append(pro)

            elif date < pro.process_start:
                before.append(pro)

            elif date > pro.process_completed:
                after.append(pro)

            else:
                progress.append(pro)

        gh_repo = gh.get_repo(project.repository_id)

        issues = [_Issue(issue.title, issue.html_url) for issue in gh_repo.get_issues()]
        branches = [branch.name for branch in gh_repo.get_branches()]

        repositories = [repo for repo in gh.get_user().get_repos()]

        histories = History.objects.filter(project=project).order_by('-id')

        persons = _assign_process(processes)

        message = action
        action = ''

        return render(request, 'project_detail.html',
                      {'project': project, 'before': before, 'progress': progress, 'after': after,
                       'completed': completed,
                       'member': member, 'persons': persons, 'users': users, 'logs': histories, 'issues': issues,
                       'branches': branches,
                       'processes': processes, 'repositories': repositories, 'toast': message})
    else:
        raise Http404


# プロジェクトを削除
@login_required
def project_delete(request, pk):
    # 削除するプロジェクト
    project = get_object_or_404(Project, pk=pk)

    if project.leader == request.user:

        for process in Process.objects.filter(parent=project):
            _process_deleted(process.pk)

        for assign in Assign.objects.filter(project=project):
            assign.delete()

        for history in History.objects.filter(project=project):
            history.delete()

        project.delete()

        return redirect('project_list')

    else:
        raise Http404


@login_required()
def project_complete(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if project.leader == request.user:
        project.is_completed = True
        project.save()

        for recruitment in Recruitment.objects.filter(project=project):
            recruitment.delete()

        global action
        action = 'project-complete'

        return redirect('project_list')

    else:
        raise Http404


# プロセスを完了
@login_required()
def process_complete(request, pk):
    process = get_object_or_404(Process, pk=pk)
    project = process.parent



    if project.leader == request.user:
        process.completed_process = True
        process.save()

        global action
        action = 'process-complete'

        return redirect('project_detail', pk=project.pk)

    else:
        raise Http404


# プロセスを削除
@login_required
def process_delete(request, pk):
    process = get_object_or_404(Process, pk=pk)
    project = process.parent

    if project.leader == request.user:
        _process_deleted(pk)
        return redirect('project_detail', pk=project.pk)

    else:
        raise Http404


# プロフィール詳細
# TODO: リポジトリの情報をクラスではなく配列の入れ子で保持する（暫定）
@login_required
def profile_detail(request, user):
    star_sum = []
    repositories = []
    watches = []

    gh = _get_gitHub(CustomUser.objects.get(username=user))

    introduction = gh.get_user().bio

    for repo in gh.get_user().get_repos():
        repositories.append(_Repository(repo.name, repo.html_url, repo.stargazers_count, repo.updated_at))

        if repo.stargazers_count > 0:
            star_sum.append('')

    for watch in gh.get_user().get_watched():
        watches.append(_Watched(watch.name, watch.html_url))

    return render(request, 'profile.html',
                  {'watches': watches, 'star_sum': star_sum, 'repositories': repositories, 'introduction': introduction})


# 招待一覧
@login_required
def invitation_list(request):
    invitations = Invitation.objects.filter(reception_user=request.user)
    message = Message.objects.filter(reception_user=request.user)
    global action


    if request.method == 'POST':
        if 'invitation_yes' in request.POST:
            invitation = get_object_or_404(Invitation, pk=request.POST['pk'])
            project = invitation.project

            assign = Assign(project=project, user=request.user)
            assign.save()

            invitation.delete()

            action = 'invitation-yes'

            return redirect('Message')

        if 'invitation_no' in request.POST:
            invitation = get_object_or_404(Invitation, pk=request.POST['pk'])
            invitation.delete()

            action = 'invitation-no'

            return redirect('Message')

        if 'application_yes' in request.POST:
            message = get_object_or_404(Message, pk=request.POST['pk'])
            project = message.project

            assign = Assign(project=project, user=message.send_user)
            assign.save()

            message.delete()

            action = 'application-yes'

            return redirect('Message')

        if 'application_no' in request.POST:
            message = get_object_or_404(Message, pk=request.POST['pk'])
            message.delete()

            action = 'application-no'

            return redirect('Message')

    toast = action
    action = ''

    return render(request, 'Message.html', {'invitations': invitations, 'message': message, 'toast': toast})



@login_required
def lounge(request):
    assigns = Assign.objects.filter(user=request.user).values('project')
    projects = []

    for assign in assigns:
        projects.append(Project.objects.get(pk=assign['project']))

    recruitment = Recruitment.objects.exclude(project__in=projects)

    if request.method == 'POST':
        recruitment = Recruitment.objects.get(pk=request.POST['pk'])
        message = Message(send_user=request.user, reception_user=recruitment.recruiter, project=recruitment.project,
                          title=request.POST['title'], text=request.POST['reason'])

        message.save()

        return redirect('lounge')

    return render(request, 'lounge.html', {'recruitment': recruitment})