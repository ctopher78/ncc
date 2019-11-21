"""
Most of the code in this library comes directly from here:
https://nbviewer.jupyter.org/gist/jiffyclub/10809459

"""

import os
from datetime import datetime

import github3


def split_one(path):
    """
    Utility function for splitting off the very first part of a path.
    
    Parameters
    ----------
    path : str
    
    Returns
    -------
    head, tail : str
    
    Examples
    --------
    >>> split_one('a/b/c')
    ('a', 'b/c')
    >>> split_one('d')
    ('', 'd')
    
    """
    s = path.split('/', 1)
    if len(s) == 1:
        return '', s[0]
    else:
        return tuple(s)


class File(object):
    """
    Represents a file/blob in the repo.
    
    Parameters
    ----------
    name : str
        Name of this file. Should contain no path components.
    mode : str
        '100644' for regular files, 
        '100755' for executable files.
    sha : str
        Git sha for an existing file, 
        omitted or None for a new/changed file.
    content : str
        File's contents as text. 
        Omitted or None for an existing file,
        must be given for a changed or new file.
    
    """
    def __init__(self, name, mode, sha=None, content=None):
        self.name = name
        self.mode = mode
        self.sha = sha
        self.content = content
    
    def create_blob(self, repo):
        """
        Post this file to GitHub as a new blob.
        
        If this file is unchanged nothing will be done.
        
        Parameters
        ----------
        repo : github3.repos.repo.Repository
            Authorized github3.py repository instance.
        
        Returns
        -------
        dict
            Dictionary of info about the blob:
            
            path: blob's name
            type: 'blob'
            mode: blob's mode
            sha: blob's up-to-date sha
            changed: True if a new blob was created
        
        """
        if self.sha:
            # already up to date
            print('Blob unchanged for {}'.format(self.name))
            changed = False
        else:
            assert self.content is not None
            print('Making blob for {}'.format(self.name))
            self.sha = repo.create_blob(self.content, encoding='utf-8')
            changed = True
        
        return {'path': self.name,
                'type': 'blob',
                'mode': self.mode,
                'sha': self.sha,
                'changed': changed}


class Directory(object):
    """
    Represents a directory/tree in the repo.
    
    Parameters
    ----------
    name : str
        Name of directory. Should not contain any path components.
    sha : str
        Hash for an existing tree, omitted or None for a new tree.
    
    """
    def __init__(self, name, sha=None):
        self.name = name
        self.sha = sha
        self.files = {}
        self.directories = {}
        self.changed = False
    
    def add_directory(self, name, sha=None):
        """
        Add a new subdirectory or return an existing one.
        
        Parameters
        ----------
        name : str
            If this contains any path components new directories
            will be made to a depth necessary to construct the full path.
        sha : str
            Hash for an existing directory, omitted or None for a new directory.
        
        Returns
        -------
        `Directory`
            Reference to the named directory.
            If `name` contained multiple path components only the
            reference to the last directory referenced is returned.
        
        """
        head, tail = split_one(name)
        if head and head not in self.directories:
            self.directories[head] = Directory(head)
        
        elif not head:
            # the input directory is a child of the current directory
            if name not in self.directories:
                self.directories[name] = Directory(name, sha)
            return self.directories[name]
        
        return self.directories[head].add_directory(tail, sha)
    
    def add_file(self, name, mode, sha=None, content=None):
        """
        Add a new file. An existing file with the same name
        will be replaced.
        
        Parameters
        ----------
        name : str
            Name of file. If it contains path components new
            directories will be made as necessary until the
            file can be made in the appropriate location.
        mode : str
            '100644' for regular files, 
            '100755' for executable files.
        sha : str
            Git hash for file. Required for existing files,
            omitted or None for new files.
        content : str
            Content of a new or changed file. Omit for existing files.
        
        Returns
        -------
        `File`
        
        """
        head, tail = os.path.split(name)
        if not head:
            # this file belongs in this directory
            if mode is None:
                if tail in self.files:
                    # we're getting an update to an existing file
                    assert content is not None
                    mode = self.files[tail].mode
                    assert mode
                else:
                    raise ValueError('Adding a new file with no mode.')
                    
            self.files[tail] = File(name, mode, sha, content)
        else:
            self.add_directory(head).add_file(tail, mode, sha, content)
    
    def delete_file(self, name):
        """
        Delete a named file.
        
        Parameters
        ----------
        name : str
            Name of file to delete. May contain path components.
        
        """
        head, tail = os.path.split(name)
        
        if not head:
            # should be in this directory
            del self.files[tail]
            self.changed = True
        else:
            self.add_directory(head).delete_file(tail)
    
    def create_tree(self, repo):
        """
        Post a new tree to GitHub.
        
        If this directory and everything in/below it 
        are unchanged nothing will be done.
        
        Parameters
        ----------
        repo : github3.repos.repo.Repository
            Authorized github3.py repository instance.
        
        Returns
        -------
        tree_info : dict
            'path': directory's name
            'mode': '040000'
            'sha': directory's up-to-date hash
            'type': 'tree'
            'changed': True if a new tree was posted to GitHub
        
        """
        tree = [f.create_blob(repo) for f in self.files.values()]
        tree = tree + [d.create_tree(repo) for d in self.directories.values()]
        tree = list(filter(None, tree))

        if not tree:
            # nothing left in this directory, it should be discarded
            return None

        # have any subdirectories or files changed (or been deleted)?
        changed = any(t['changed'] for t in tree) or self.changed
        
        if changed:
            print('Creating tree for {}'.format(self.name))
            tree = [{k: v for k, v in t.items() if k != 'changed'} for t in tree]
            self.sha = repo.create_tree(tree).sha
        else:
            print('Tree unchanged for {}'.format(self.name))
        assert self.sha
        return {'path': self.name,
                'mode': '040000',
                'sha': self.sha,
                'type': 'tree',
                'changed': changed}


class Github():
    def __init__(self, token, org, repository, branch):
        self.github = github3.login(token=token)
        self.org = org
        self.repository = repository
        self.branch = branch
    
    def push(self, configs):
        repo = self.github.repository(self.org, self.repository)
        sha = repo.branch("master").commit.sha
        tree = repo.tree(sha, recursive=True)

        for t in tree.tree:
            print(t.path, t.mode, t.type)

        trees = [h for h in tree.tree if h.type == 'tree']
        blobs = [h for h in tree.tree if h.type == 'blob']

        root = Directory('', sha)

        for h in trees:
            root.add_directory(h.path, h.sha)

        for h in blobs:
            root.add_file(h.path, h.mode, h.sha)

        for config in configs:
            root.add_file(config["path"], config["mode"], content=config["content"])

        root_info = root.create_tree(repo)

        new_commit = repo.create_commit(
            "{} - Config Updates Commit".format(datetime.now().strftime("%m/%d/%Y %H:%M:%S")),
            tree=root_info["sha"],
            parents=[sha])

        ref = repo.ref('heads/{}'.format("master"))
        result = ref.update(new_commit.sha)

        if result:
            print("Push to Github Successful!")
        else:
            print("Push to Github Failed!")