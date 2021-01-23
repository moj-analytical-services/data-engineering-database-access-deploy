# Data Engineering Database Access Deploy

## Introduction

This repository contains a Pulumi project that creates AWS CodeBuild
infrastructure to perform continuous integration and continuous deployment on
the
[data-engineering-database-access](https://github.com/moj-analytical-services/data-engineering-database-access)
repository.

## Prerequisites

To work with this repository, you must have the following installed:

- [git-crypt](https://github.com/AGWA/git-crypt) – see the
  [git-crypt README](.git-crypt/README.md) for further information on how to
  install git-crypt and use it with this repository
- [Python 3.6 or later](https://www.python.org/downloads/)
- [Pulumi](https://www.pulumi.com/docs/get-started/install/)

You should also:

1.  Create a virtual environment:

        python -m venv venv

2.  Activate the environment:

        source venv/bin/activate

3.  Install dependencies:

        pip install -r requirements.txt

## Usage

To update the Pulumi project:

1.  Create an AWS Vault shell session with the `restricted-admin@data` role. For
    more information, see the
    [analytical-platform-iam](https://github.com/ministryofjustice/analytical-platform-iam)
    repository.

2.  Activate your virtual environment:

        source venv/bin/activate

3.  Log in to the Pulumi backend:

        pulumi login -c s3://data-engineering-pulumi.analytics.justice.gov.uk

4.  Select the `de-database-access-deploy` stack:

        pulumi stack select de-database-access-deploy

5.  Preview any changes (optional):

        pulumi preview [--diff]

6.  Deploy any changes:

        pulumi up

## git-crypt

This repository uses git-crypt to encrypt secrets. For more information, see the
[git-crypt README](./.git-crypt/README.md).

## Licence

[MIT Licence](LICENCE.md)
