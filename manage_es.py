from elasticsearch import Elasticsearch

es = Elasticsearch()
es.indices.create('hoe')