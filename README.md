# Historiography of the Ottoman Empire

Live Site: [https://hoe.ub.rub.de](https://hoe.ub.rub.de)

This is the platform for the joint project by the [University Library Bochum](http://www.ub.rub.de) and
[the chair in History of the Ottoman Empire and Modern Turkey](http://www.ort.ruhr-uni-bochum.de/index.html.en) of
[Ruhr-University Bochum](http://www.rub.de) [funded by the DFG](http://gepris.dfg.de/gepris/projekt/249662419). The
platform enables researchers to register primary and secondary literature and to search it with state of the art search
engine technology. The web application is implemented with [Flask](http://flask.pocoo.org/) and as the search engine we
employ [Solr](http://lucene.apache.org/solr/) while the depiction oof cartographic data is based on
[OpenStreetMap](http://www.openstreetmap.org) and the [Leaflet](http://leafletjs.com/) library.

To host your own instance of the platform, you should first clone this repository.

Make a new virtual environment in a Python 3 installation.

Install the dependencies into this environment with ```pip install -r requirements.txt```.

We recommend you run the platform with ```uwsgi``` which can be started like this:

```uwsgi -s /tmp/hoe.sock -w hoe:app --master --processes=2
--harakiri=20 --max-requests=5000 --vacuum --daemonize=/tmp/hoe.log```.

Download a recent version of Solr and move the directories under the platform's ```solr``` directory into the
```server/solr``` directory of your Solr installation. You can then start Solr with ```bin/solr start```.