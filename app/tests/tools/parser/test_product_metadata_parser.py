# type: ignore
from tools.parser.models.product_metadata import ProductMetadata
from tools.parser.product_metadata_parser import extract_product_metadata

JSON_LD_HTML = """
 <html>
  <head>
    <title>Executive Anvil</title>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org/",
      "@type": "Product",
      "name": "Executive Anvil",
      "description": "Sleeker than ACME's Classic Anvil, the Executive Anvil is perfect for the business traveler looking for something to drop from a height.", # noqa: E501
      "review": {
        "@type": "Review",
        "reviewRating": {
          "@type": "Rating",
          "ratingValue": 4,
          "bestRating": 5
        },
        "author": {
          "@type": "Person",
          "name": "Fred Benson"
        }
      },
      "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": 4.4,
        "reviewCount": 89
      }
    }
    </script>
  </head>
  <body>
  </body>
</html>
"""

RDFA_HTML = """
 <html>
  <head>
    <title>Executive Anvil</title>
  </head>
  <body>
    <div typeof="schema:Product">
        <div rel="schema:review">
          <div typeof="schema:Review">
            <div rel="schema:reviewRating">
              <div typeof="schema:Rating">
                <div property="schema:ratingValue" content="4"></div>
                <div property="schema:bestRating" content="5"></div>
              </div>
            </div>
            <div rel="schema:author">
              <div typeof="schema:Person">
                <div property="schema:name" content="Fred Benson"></div>
              </div>
            </div>
          </div>
        </div>
        <div property="schema:name" content="Executive Anvil"></div>
        <div property="schema:description" content="Sleeker than ACME's Classic Anvil, the Executive Anvil is perfect for the business traveler looking for something to drop from a height."></div> # noqa: E501
        <div rel="schema:aggregateRating">
          <div typeof="schema:AggregateRating">
            <div property="schema:reviewCount" content="89"></div>
            <div property="schema:ratingValue" content="4.4"></div>
          </div>
        </div>
      </div>
  </body>
</html>
"""

MICRODATA_HTML = """
 <html>
  <head>
    <title>Executive Anvil</title>
  </head>
  <body>
  <div>
    <div itemtype="https://schema.org/Product" itemscope>
      <meta itemprop="name" content="Executive Anvil" />
      <meta itemprop="description" content="Sleeker than ACME's Classic Anvil, the Executive Anvil is perfect for the business traveler looking for something to drop from a height." />
      <div itemprop="aggregateRating" itemtype="https://schema.org/AggregateRating" itemscope>
        <meta itemprop="reviewCount" content="89" />
        <meta itemprop="ratingValue" content="4.4" />
      </div>
      <div itemprop="review" itemtype="https://schema.org/Review" itemscope>
        <div itemprop="author" itemtype="https://schema.org/Person" itemscope>
          <meta itemprop="name" content="Fred Benson" />
        </div>
        <div itemprop="reviewRating" itemtype="https://schema.org/Rating" itemscope>
          <meta itemprop="ratingValue" content="4" />
          <meta itemprop="bestRating" content="5" />
        </div>
      </div>
    </div>
  </div>
  </body>
</html>
"""


def test_extract_json_ld():
    metadata = extract_product_metadata(JSON_LD_HTML)
    assert isinstance(metadata, ProductMetadata)
    assert metadata.name == "Executive Anvil"
    assert (
        metadata.description
        == "Sleeker than ACME's Classic Anvil, the Executive Anvil is perfect for the business traveler looking for something to drop from a height."  # noqa: E501
    )
    assert metadata.aggregateRating.ratingValue == 4.4
    assert metadata.aggregateRating.reviewCount == 89
    assert len(metadata.review) == 1
    assert metadata.review[0].reviewRating.ratingValue == 4
    assert metadata.review[0].reviewRating.bestRating == 5
    assert metadata.review[0].author == "Fred Benson"


def test_extract_rdfa():
    metadata = extract_product_metadata(RDFA_HTML)
    assert isinstance(metadata, ProductMetadata)
    assert metadata.name == "Executive Anvil"
    assert (
        metadata.description
        == "Sleeker than ACME's Classic Anvil, the Executive Anvil is perfect for the business traveler looking for something to drop from a height."
    )
    assert metadata.aggregateRating.ratingValue == 4.4
    assert metadata.aggregateRating.reviewCount == 89
    assert len(metadata.review) == 1
    assert metadata.review[0].reviewRating.ratingValue == 4
    assert metadata.review[0].reviewRating.bestRating == 5
    assert metadata.review[0].author == "Fred Benson"


def test_extract_microdata():
    metadata = extract_product_metadata(MICRODATA_HTML)
    assert isinstance(metadata, ProductMetadata)
    assert metadata.name == "Executive Anvil"
    assert (
        metadata.description
        == "Sleeker than ACME's Classic Anvil, the Executive Anvil is perfect for the business traveler looking for something to drop from a height."
    )
    assert metadata.aggregateRating.ratingValue == 4.4
    assert metadata.aggregateRating.reviewCount == 89
    assert len(metadata.review) == 1
    assert metadata.review[0].reviewRating.ratingValue == 4
    assert metadata.review[0].reviewRating.bestRating == 5
    assert metadata.review[0].author == "Fred Benson"


def test_invalid_html():
    metadata = extract_product_metadata("<html><body>No product data</body></html>")
    assert metadata is None


def test_malformed_json_ld():
    html = """
    <html><head><script type="application/ld+json">
    {invalid json}
    </script></head></html>
    """
    metadata = extract_product_metadata(html)
    assert metadata is None
