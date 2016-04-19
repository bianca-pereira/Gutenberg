"""Module for implementations of the MetadataExtractor interface."""


from __future__ import absolute_import

from rdflib.term import Literal
from rdflib.term import URIRef

from gutenberg._domain_model.vocabulary import DCTERMS
from gutenberg._domain_model.vocabulary import PGTERMS
from gutenberg._domain_model.vocabulary import RDFNAMESPACE
from gutenberg._util.abc import abstractclassmethod
from gutenberg.query.api import MetadataExtractor


class _SimplePredicateRelationshipExtractor(MetadataExtractor):
    """Extracts any sort of meta-data that is directly connected to a text via
    a simple predicate relationship or a simple predicate-path relationship.

    """
    @abstractclassmethod
    def predicate(cls):
        """Returns the predicate relationship that connects the text with the
        meta-data value to extract. This should be a RDF Term or Path object.

        """
        raise NotImplementedError

    @classmethod
    def get_metadata(cls, etextno):
        etext = cls._etext_to_uri(etextno)
        query = cls._metadata()[etext:cls.predicate():]
        return frozenset(result.toPython() for result in query)

    @classmethod
    def get_etexts(cls, requested_value):
        query = cls._metadata()[:cls.predicate():cls.contains(requested_value)]
        return frozenset(cls._uri_to_etext(result) for result in query)

class AuthorExtractor(_SimplePredicateRelationshipExtractor):
    """Extracts book authors.

    """
    @classmethod
    def feature_name(cls):
        return 'author'

    @classmethod
    def predicate(cls):
        return DCTERMS.creator / PGTERMS.alias

    @classmethod
    def contains(cls, value):
        return Literal(value)

class TitleExtractor(_SimplePredicateRelationshipExtractor):
    """Extracts book titles.

    """
    @classmethod
    def feature_name(cls):
        return 'title'

    @classmethod
    def predicate(cls):
        return DCTERMS.title

    @classmethod
    def contains(cls, value):
        return Literal(value)


class FormatURIExtractor(_SimplePredicateRelationshipExtractor):
    """Extracts book format URIs.

    """
    @classmethod
    def feature_name(cls):
        return 'formaturi'

    @classmethod
    def predicate(cls):
        return DCTERMS.hasFormat

    @classmethod
    def contains(cls, value):
        return URIRef(value)

class _ComplexPredicateRelationshipExtractor(MetadataExtractor):
    """Extracts any sort of meta-data that connected through two-level
    relationships.

    """

    @abstractclassmethod
    def predicate(cls):
        """Returns the predicate that connects the text with another
        entity (e.g. subject, language).

        """
        raise NotImplementedError

    @abstractclassmethod
    def secondary_predicate(cls):
        """Extracts any sort of meta-data that is directly connected to a text via
        a simple predicate relationship or a simple predicate-path relationship.

        """
        raise NotImplementedError

    @classmethod
    def get_metadata(cls, etextno):
        etext = cls._etext_to_uri(etextno)
        query = cls._metadata()[etext:cls.predicate():]

        metadata = set()
        for result in query:
            query2 = cls._metadata()[result::]
            metadata.update(set((s.toPython(),p.toPython()) for s,p in query2))

        # TODO: Improve presentation
        return frozenset(metadata)

    @classmethod
    def get_etexts(cls, requested_value):
        query = cls._metadata()[:cls.secondary_predicate():cls.contains(requested_value)]

        etext = set()
        for result in query:
            query2 = cls._metadata()[:cls.predicate():result]
            etext.update(set(cls._uri_to_etext(result) for result in query2))

        return frozenset(etext)


class SubjectExtractor(_ComplexPredicateRelationshipExtractor):
    """Extracts book subjects.

    """
    @classmethod
    def feature_name(cls):
        return 'subject'

    @classmethod
    def predicate(cls):
        return DCTERMS.subject

    @classmethod
    def secondary_predicate(cls):
        return RDFNAMESPACE.value

    @classmethod
    def contains(cls,value):
        return Literal(value)

class LanguageExtractor(_ComplexPredicateRelationshipExtractor):
    """Extracts book language.

    """
    @classmethod
    def feature_name(cls):
        return 'language'

    @classmethod
    def predicate(cls):
        return DCTERMS.language

    @classmethod
    def secondary_predicate(cls):
        return RDFNAMESPACE.value

    @classmethod
    def contains(cls,value):
        return Literal(value,datatype=DCTERMS.RFC4646)