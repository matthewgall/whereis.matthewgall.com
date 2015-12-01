# whereis.matthewgall.com

![](https://badge.imagelayers.io/matthewgall/whereis.matthewgall.com:latest.svg)

Inspired by a creation of [Josh McMillan](https://twitter.com/jshmc) to allow his family to track him while he circumnavigated the world, I decided to create my own. whereis.matthewgall.com is a Python / Javascript powered location service, which exposes a simple submission API.

## Introducing whereis.matthewgall.com
Powered by Python and bottle, whereis.matthewgall.com is quick and simple to deploy, using all the power of [Docker](https://docker.io) you can be up and running in one command!

## Deploying
Deploying whereis.matthewgall.com is easy using Docker:

    docker run -e SERVER_HOST=0.0.0.0 -e DATABASE_URL=postgres://example.com/lol -e APP_TOKEN=example -p 80:5000 matthewgall/whereis.matthewgall.com

Honestly, that simple (and none of that one line wget direct to your terminal)

## Licence

    The MIT License (MIT)

    Copyright (c) 2015 Matthew Gall

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
