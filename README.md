## Description
Pull the latest version information for any set of packages.

Given the file `requirements.txt`:
```c
awscli==1.3.6
requests==2.0.0
tqdm==4.42.0
toml==0.10.0
```

Running the Alpine Docker container: `docker run -v $PWD:/app rererecursive/latest-packages python3 main.py file=requirements.txt type=pip`:
```
Fetching version information for 4 packages...
100%|█████████████████████████████████████████████| 4/4 [00:01<00:00,  2.76it/s]

Available:
  awscli    1.3.6  =>  1.9.9
  requests  2.0.0  =>  2.9.2

Latest [OK]:
  toml      0.10.0
  tqdm      4.42.0

Wrote latest package versions to: /tmp/requirements.txt
```

From inside a Jenkins pipeline:
```groovy
pipeline {
    // ...

    stage('Check for new packages') {
        getLatestPackages(
            file: 'requirements.txt'
            type: 'pip',
            ignore: ['awscli', 'numpy'],  // Ignore these packages from the search
            overwrite: true     // Overwrite the packages file with the latest versions
        )
    }
    // ...
}
```

## Package support
- NodeJS
- PHP
- Python
- Ruby
- Rust

It works by querying the APIs for each language's package manager. The URLs can be viewed in `main.py`.

## Purpose
This is intended to be added to an existing CI/CD process. There is generally a debate regarding locking versions to specific numbers vs using the 'latest' version.  
This allows us to do both.  
The idea is to lock versions to specific numbers, but to get notified (or automatically update and build) if new versions appear.  
We then get the best of both worlds: builds are repeatable and won't suddenly break, and packages can also get their latest features and fixes.

## Options
Additional options to the Python script:  
`overwrite=true | [false]` - overwrite the original file that contains the package versions  
`ignore=awscli,numpy` - ignore specific packages from being searched for new versions  

