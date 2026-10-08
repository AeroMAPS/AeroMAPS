# Development workflow

## Developing in a new branch

One you have your local clone of the project

```bash
git clone
```
Synchronize your main branch with the `upstream/main branch`

```bash
git checkout main
git fetch upstream
git pull
```

Whether your developing a new feature or fixing a bug, it is always advised to create 
a new branch. Never work on the main branch! The main branch is supposed to be a 
functional branch, if you are commit work in progress changes, it can
lead breaking something. 

create a new branch were you will work on your changes:

```bash
git checkout -b name_of_the_branch
```

and your set to work on your changes!

When you are making changes on your code, use Git to do the version control. When you
are done editing changes use `git add` to add the changed file and `git commit`. When 
committing, is a good practice to use a good descriptive message for your commit

```bash
git add modified_files
git commit -m "a descriptive message about your changes"
```

Alternatively your can use the integrated git workflow of your IDE. Check your IDE's 
documentation to learn how to use it.

Note that pre-commit might reformat your code when committing, if this happens you to do 
`git add` and `git commit` again.

Once your changes are done push your changes to the upstream github with 

```bash
git push -u origin name_of_the_branch
```
if it is the first time your pushing, or 

```bash
git push
```

if your branch has already been published before. 

The process of pushing your branch can also be done 
through your IDE's interface.

## Pull request

Before opening a `Pull Request` (PR) and requesting for a review make sure that your 
pull request covers the [PR checklist](#pull-request-checklist).

### Pull request checklist

Before open a PR make sure that:

- All existing tests pass
- Any added line to the code is tested
- Any feature, or change is properly documented
- Your branch is up to date with the main branch

### Opening a pull request

Once your modifications, tests and documentation is done, you can open a 
`Pull Request` (PR) to merge your changes into the main branch. This can be done
in different ways.

1. When you push a commit, your git log will suggest an url to open a PR. By clicking
on it, a new window on will pop in your browser to open a PR on github.

2. By creating the PR directly on github.

3. From the terminal you can open a PR with

```bash
gh pre create --base main --head name_of_the_branch --title "The title of your PR" --body "Description of your PR"
```

We recommend using the github interface.

### Drafting a pull request

Sometimes it is useful to have feedback on your modification while they are still a
work in progress. You can set a PR as a draft so that other collaborators can have
visibility on your changes while they are still in progress. Once you are done, you can
set it as ready to merge and request a reviewer.

### Pull request review

Every PR goes through a review process. Once your PR is ready to merge, request for it 
to be review by a collaborator. Your reviewer might suggest changes to the PR, fixes,
etc.

## Keeping your branch synchronized with main and rebasing

When working in a collaborative project, there can be many parallel branches
and developments which can merge into the main branch while you are working on your
modifications. 

It is recommended to regularly keep your branch synchronized with the main branch to
avoid diverging or handling conflicts at the moment of merging into the main branch.

To keep your branch synchronized, checkout the main branch,
 pull the latest modifications, checkout your branch and then rebase.

```bash
git checkout -b your_branch_name
git rebase main 
```

When rebasing you might encounter conflicts due to modifications done on a file that
you are also modifying. You will have to solve this conflicts manually before
continuing. 


