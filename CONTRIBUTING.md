## Contributing Guidelines

First off, thank you for considering contributing to `Robyn`. This guide details all the general information that one should know before contributing to the project.
Please stick as close as possible to the guidelines. That way, we ensure that you have a smooth experience contributing to this project.

### General Rules:

These are, in general, rules that you should be following while contributing to an Open-Source project :

- Be Nice, Be Respectful (BNBR)
- Check if the Issue you created, exists or not.
- While creating a new issue, make sure you describe the issue clearly.
- Make proper commit messages and document your PR well.
- Always add comments in your Code and explain it at points if possible, add Doctest.
- Always create a Pull Request from a Branch; Never from the Main.
- Follow proper code conventions because writing clean code is important.
- Issues would be assigned on a "First Come, First Served" basis.
- Do mention (@sansyrox) the project maintainer if your PR isn't reviewed within a few days.

## First time contributors:

Pushing files in your own repository is easy, but how to contribute to someone else's project? If you have the same question, then below are the steps that you can follow
to make your first contribution in this repository.

### Pull Request

**1.** The very first step includes forking the project. Click on the `fork` button as shown below to fork the project.
<br><br><img src="https://i.imgur.com/7wapvt2.png" width="750" /><br>

**2.** Clone the forked repository. Open up the GitBash/Command Line and type

```
git clone https://github.com/<YOUR_USER_NAME>/robyn.git
```

**3.** Navigate to the project directory.

```
cd robyn
```

**4.** Add a reference to the original repository.

```
git remote add upstream https://github.com/sansyrox/robyn.git
```

**5.** See latest changes to the repo using

```
git remote -v
```

**6.** Create a new branch.

```
git checkout -b <YOUR_BRANCH_NAME>
```

**7.** Always take a pull from the upstream repository to your main branch to keep it even with the main project. This will save you from frequent merge conflicts.

```
git pull upstream main
```

**8.** You can make the required changes now. Make appropriate commits with proper commit messages.

**9.** Add and then commit your changes.

```
git add .
```

```
git commit -m "<YOUR_COMMIT_MESSAGE>"
```

**10.** Push your local branch to the remote repository.

```
git push -u origin <YOUR_BRANCH_NAME>
```

**11.** Once you have pushed the changes to your repository, go to your forked repository. Click on the `Compare & pull request` button as shown below.
<br><br><img src="https://hisham.hm/img/posts/github-comparepr.png" width="750" /><br>

**12.** The image below is what the new page would look like. Give a proper title to your PR and describe the changes made by you in the description box.(Note - Sometimes there are PR templates which are to be filled as instructed.)
<br><br><img src="https://github.blog/wp-content/uploads/2019/02/draft-pull-requests.png?fit=1354%2C780" width="750" /><br>

**13.** Open a pull request by clicking the `Create pull request` button.

`Voila, you have made your first contribution to this project`

## Issue

- Issues can be used to keep track of bugs, enhancements, or other requests. Creating an issue to let the project maintainers know about the changes you are planning to make before raising a PR is a good open-source practice.
  <br>

Let's walk through the steps to create an issue:

**1.** On GitHub, navigate to the main page of the repository. [Here](https://github.com/sansyrox/robyn.git) in this case.

**2.** Under your repository name, click on the `Issues` button.
<br><br><img src="https://www.stevejgordon.co.uk/wp-content/uploads/2018/01/GitHubIssueTab.png" width="750" /><br>

**3.** Click on the `New issue` button.
<br><br><img src="https://miro.medium.com/max/3696/1*8jiGiKhMdVQDycWSAbjB8A.png" width="750" /><br>

**4.** Select one of the Issue Templates to get started.
<br><br><img src="https://i.imgur.com/xz2KAwU.png" width="750" /><br>

**5.** Fill in the appropriate `Title` and `Issue description` and click on `Submit new issue`.
<br><br><img src="https://i.imgur.com/XwjtGG1.png" width="750" /><br>

### Tutorials that may help you:

- [Git & GitHub Tutorial](https://www.youtube.com/watch?v=RGOj5yH7evk)
- [Resolve merge conflict](https://docs.github.com/en/free-pro-team@latest/github/collaborating-with-issues-and-pull-requests/resolving-a-merge-conflict-on-github)
