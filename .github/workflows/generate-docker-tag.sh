#!/bin/bash


# GITHUB_REF: refs/heads/<branch_name>, refs/tags/<tag_name>
if [ ! -z $GITHUB_REF ]; then
    TRIGGER_TYPE=$(echo $GITHUB_REF | cut -d '/' -f2)
    NAME=$(echo $GITHUB_REF | cut -d '/' -f3)

    echo $GITHUB_REF
    if [ $TRIGGER_TYPE = "heads" ]; then
        export PUSH=true
        if [ $NAME = "master" ]; then
            export DOCKER_TAG=prod
            export DJANGO_ENV=production
            echo $FIREBASE_SERVICE_ACCOUNT_KEY_PROD > firebaseServiceAccountKey.json
        elif [ $NAME = "develop" ]; then
            # Docker tag에 /가 들어갈 수 없어서 -로 변경
            export DOCKER_TAG=develop
            export DJANGO_ENV=development
            echo $FIREBASE_SERVICE_ACCOUNT_KEY_DEV > firebaseServiceAccountKey.json
        else
            export DOCKER_TAG=manual
            export DJANGO_ENV=development
            export PUSH=true
            echo $FIREBASE_SERVICE_ACCOUNT_KEY_DEV > firebaseServiceAccountKey.json
        fi
    elif [ $TRIGGER_TYPE = "tags" ]; then
        export PUSH=true
        export DOCKER_TAG=$NAME
        export DJANGO_ENV=production
        echo $FIREBASE_SERVICE_ACCOUNT_KEY_PROD > firebaseServiceAccountKey.json

    elif [ $TRIGGER_TYPE = "pull" ]; then
        export PUSH=true
        export DOCKER_TAG="pr$NAME"
        export DJANGO_ENV=development
        echo $FIREBASE_SERVICE_ACCOUNT_KEY_DEV > firebaseServiceAccountKey.json

    fi
fi

echo $PUSH $TRIGGER_TYPE $DJANGO_ENV $DOCKER_TAG
