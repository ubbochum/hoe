# Historiography of Ottoman Europe

Live Site: [https://hoe.ub.rub.de](https://hoe.ub.rub.de)

This is the platform for the joint project by the [University Library Bochum](http://www.ub.rub.de) and
[the chair in History of the Ottoman Empire and Modern Turkey](http://www.ort.ruhr-uni-bochum.de/index.html.en) of
[Ruhr-University Bochum](http://www.rub.de) [funded by the DFG](http://gepris.dfg.de/gepris/projekt/249662419). The
platform enables researchers to register primary and secondary literature and to search it with state of the art search
engine technology. The web application is implemented with [Flask](http://flask.pocoo.org/) and as the search engine we
employ [Solr](http://lucene.apache.org/solr/) while the depiction of cartographic data is based on
[OpenStreetMap](http://www.openstreetmap.org) and the [Leaflet](http://leafletjs.com/) library.

To host your own instance of the platform, you should first clone this repository.

Make a new virtual environment in a Python 3 installation.

Install the dependencies into this environment with ```pip install -r requirements.txt```.

We recommend you run the platform with ```uwsgi``` which can be started like this:

```uwsgi -s /tmp/hoe.sock -w hoe:app --master --processes=2
--harakiri=20 --max-requests=5000 --vacuum --daemonize=/tmp/hoe.log```.

Download a recent version of Solr and move the directories under the platform's ```solr``` directory into the
```server/solr``` directory of your Solr installation. You can then start Solr with ```bin/solr start```.

## License

The MIT License

Copyright 2015-2016 University Library Bochum <ottomanhistoriography@ruhr-uni-bochum.de>.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
