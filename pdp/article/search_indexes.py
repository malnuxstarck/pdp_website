from haystack import indexes
from pdp.article.models import Article


class ArticleIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    author = indexes.CharField(model_attr='author')
    description = indexes.CharField(model_attr='description')
    pubdate = indexes.DateTimeField(model_attr='pubdate')
    txt = indexes.CharField(model_attr='text')

    def get_model(self):
        return Article

    def index_queryset(self, using=None):
        '''Used when the entire index for model is updated.'''
        return self.get_model().objects\
            .filter(is_visible=True)