#! /usr/bin/env bash

python setup.py compile_catalog

if [ ! -f openfisca_bot ]; then
    openssl aes-256-cbc -K $encrypted_67b95433b01c_key -iv $encrypted_67b95433b01c_iv -in openfisca_bot.enc -out openfisca_bot -d
    openssl aes-256-cbc -K $encrypted_3fddb3da1568_key -iv $encrypted_3fddb3da1568_iv -in deploy-api.enc -out deploy-api -d
    eval "$(ssh-agent -s)"
    chmod 400 ./openfisca_bot ./deploy-api
    ssh-add ./openfisca_bot ./deploy-api
fi