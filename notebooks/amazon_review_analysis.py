import json
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import load_dataset
from loguru import logger


def load_amazon_data_to_df(category: str = "All_Beauty", split: str = "full", trust_remote_code: bool = True) -> pd.DataFrame:
    """
    Load Amazon metadata directly into DataFrame for analysis

    Args:
        category: Category name to load (e.g., 'All_Beauty')
        split: Dataset split to load
        trust_remote_code: Whether to trust remote code

    Returns:
        DataFrame with cleaned Amazon product data
    """
    logger.info(f"Loading {category} dataset...")
    dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", f"raw_meta_{category}", split=split, trust_remote_code=trust_remote_code)

    # Convert to DataFrame
    df = pd.DataFrame(dataset)

    # Clean price data - convert to numeric
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    logger.info(f"Loaded {len(df)} records")
    return df


def analyze_category_popularity(df: pd.DataFrame) -> dict:
    """
    Analyze category popularity and rating distribution

    Args:
        df: DataFrame with Amazon data (expects numeric price column)

    Returns:
        Dict with category metrics and rating distribution
    """
    # Basic metrics by category
    category_metrics = (
        df.groupby("main_category").agg({"average_rating": "mean", "rating_number": "mean", "price": ["mean", "median", "std"]}).round(2)
    )

    # Flatten multi-level columns
    category_metrics.columns = [f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col for col in category_metrics.columns]

    # Rating distribution (1-5 stars)
    bins = [0, 1.5, 2.5, 3.5, 4.5, 5.0]
    labels = ["1 star", "2 stars", "3 stars", "4 stars", "5 stars"]

    rating_dist = pd.cut(df["average_rating"].dropna(), bins=bins, labels=labels).value_counts(normalize=True)

    return {
        "category_metrics": category_metrics.to_dict(),
        "rating_distribution": rating_dist.mul(100).round(2).to_dict(),
        "missing_prices": int(df["price"].isna().sum()),
        "total_products": len(df),
    }


def analyze_details_distribution(df: pd.DataFrame) -> dict:
    """
    Analyze distribution of product attributes from details

    Args:
        df: DataFrame with Amazon data

    Returns:
        Dictionary with significant attribute distribution
    """
    analysis = {}

    # Parse details JSON if it hasn't been parsed yet
    if "details_dict" not in df.columns:
        df["details_dict"] = df["details"].apply(lambda x: json.loads(x) if isinstance(x, str) else {})

    # Collect all unique keys from details
    all_keys: set[str] = set()
    for details in df["details_dict"].dropna():
        if isinstance(details, dict):
            all_keys.update(details.keys())

    for attr in all_keys:
        # Extract values for this attribute
        values = []
        for details in df["details_dict"].dropna():
            if isinstance(details, dict) and attr in details:
                values.append(details[attr])

        # Calculate coverage
        total_products = len(df)
        products_with_attr = len(values)
        coverage = (products_with_attr / total_products) * 100

        # Only include if coverage > 1%
        if coverage > 1:
            # Convert values to pandas series for counting
            value_series = pd.Series(values)
            value_counts = value_series.value_counts().head(10).to_dict()

            analysis[attr] = {"top_values": value_counts, "coverage_percentage": f"{round(coverage, 2)}%", "unique_values": len(set(values))}

    return analysis


def analyze_attributes(df: pd.DataFrame) -> dict:
    """
    Analyze product attributes distribution

    Args:
        df: DataFrame with Amazon data (expects numeric price column)

    Returns:
        Dict with attribute analysis
    """
    analysis = {}

    # Analyze each attribute
    for attr in df.columns:
        # Skip certain columns
        if attr in ["average_rating", "rating_number", "price"]:
            continue

        # Get non-null values
        values = [v for v in df[attr] if pd.notna(v)]

        # Skip if no values
        if not values:
            continue

        # Calculate coverage
        total_products = len(df)
        products_with_attr = len(values)
        coverage = (products_with_attr / total_products) * 100

        # Only include if coverage > 1%
        if coverage > 1:
            # Convert values to pandas series for counting
            value_series = pd.Series(values)
            value_counts = value_series.value_counts().head(10).to_dict()

            analysis[attr] = {"top_values": value_counts, "coverage_percentage": f"{round(coverage, 2)}%", "unique_values": len(set(values))}

    return analysis


def analyze_media_presence(df: pd.DataFrame) -> dict:
    """
    Analyze image and video presence in product listings

    Args:
        df: DataFrame with Amazon data

    Returns:
        Dict containing:
        - image_metrics: Stats about image presence and distribution
        - video_metrics: Stats about video presence
    """
    total_products = len(df)

    # Image analysis
    def count_images(images: dict) -> int:
        # Count unique images from hi_res and large
        hi_res = {img for img in images.get("hi_res", []) if img is not None}
        large = {img for img in images.get("large", []) if img is not None}
        return len(hi_res.union(large))

    # Count images per product
    image_counts = df["images"].apply(count_images)
    has_images = image_counts > 0

    # Video analysis
    def has_video(videos: dict) -> bool:
        return bool(videos.get("url", []))

    has_videos = df["videos"].apply(has_video)

    return {
        "image_metrics": {
            "products_with_images": {"count": int(has_images.sum()), "percentage": round((has_images.sum() / total_products) * 100, 2)},
            "image_distribution": {
                "mean": round(image_counts.mean(), 2),
                "median": round(image_counts.median(), 2),
                "max": int(image_counts.max()),
                "distribution": image_counts.value_counts().sort_index().head(10).to_dict(),
            },
            "hi_res_availability": {
                "count": int(df["images"].apply(lambda x: bool(x.get("hi_res", [])) if isinstance(x, dict) else False).sum()),
                "percentage": round(
                    (df["images"].apply(lambda x: bool(x.get("hi_res", [])) if isinstance(x, dict) else False).sum() / total_products) * 100, 2
                ),
            },
        },
        "video_metrics": {
            "products_with_videos": {"count": int(has_videos.sum()), "percentage": round((has_videos.sum() / total_products) * 100, 2)}
        },
    }


def analyze_brand_distribution(df: pd.DataFrame, min_products: int = 10) -> dict:
    """
    Analyze brand presence and market concentration

    Args:
        df: DataFrame with Amazon data
        min_products: Minimum products for brand inclusion

    Returns:
        Dict containing brand distribution metrics
    """
    # Group by store (brand) and count products
    brand_counts = df["store"].value_counts()

    # Filter for brands with minimum products
    significant_brands = brand_counts[brand_counts >= min_products]

    # Calculate concentration metrics
    total_products = len(df)
    top_10_share = brand_counts.head(10).sum() / total_products * 100

    return {
        "brand_metrics": {
            "total_brands": len(brand_counts),
            "significant_brands": len(significant_brands),
            "top_10_concentration": round(top_10_share, 2),
            "top_brands": brand_counts.head(20).to_dict(),
        },
        "distribution_metrics": {
            "products_per_brand": {"mean": round(brand_counts.mean(), 2), "median": round(brand_counts.median(), 2), "max": int(brand_counts.max())}
        },
    }


def analyze_brand_performance(df: pd.DataFrame, min_reviews: int = 50, top_n: int = 20) -> dict:
    """
    Analyze brand ratings and performance

    Args:
        df: DataFrame with Amazon data
        min_reviews: Minimum reviews for brand inclusion
        top_n: Number of top brands to return

    Returns:
        Dict containing:
        - overall_metrics: General brand statistics
        - top_brands: Top N brands by review count
        - rating_distribution: Rating statistics
    """
    # Group by store (brand) and calculate metrics
    brand_metrics = df.groupby("store").agg(
        {"average_rating": ["mean", "count", "std"], "rating_number": "sum", "price": ["mean", "median", "count"]}
    )

    # Flatten column names
    brand_metrics.columns = [f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col for col in brand_metrics.columns]

    # Filter for brands with minimum reviews
    significant_brands = brand_metrics[brand_metrics["average_rating_count"] >= min_reviews]

    # Sort by total reviews for top performers
    top_brands = significant_brands.sort_values(by="rating_number_sum", ascending=False)

    return {
        "overall_metrics": {
            "total_brands": len(brand_metrics),
            "brands_analyzed": len(significant_brands),
            "review_statistics": {
                "mean_reviews_per_brand": round(significant_brands["rating_number_sum"].mean(), 2),
                "median_reviews_per_brand": round(significant_brands["rating_number_sum"].median(), 2),
            },
        },
        "top_brands": {
            brand: {
                "total_reviews": int(metrics["rating_number_sum"]),
                "average_rating": round(metrics["average_rating_mean"], 2),
                "rating_std": round(metrics["average_rating_std"], 2),
                "product_count": int(metrics["average_rating_count"]),
                "avg_price": round(metrics["price_mean"], 2) if pd.notna(metrics["price_mean"]) else None,
                "median_price": round(metrics["price_median"], 2) if pd.notna(metrics["price_median"]) else None,
                "products_with_price": int(metrics["price_count"]),
            }
            for brand, metrics in top_brands.head(top_n).to_dict("index").items()
        },
        "rating_distribution": {
            "mean": round(significant_brands["average_rating_mean"].mean(), 2),
            "median": round(significant_brands["average_rating_mean"].median(), 2),
            "std": round(significant_brands["average_rating_mean"].std(), 2),
        },
    }


def extract_key_metrics(analysis_results: dict[str, Any]) -> dict[str, Any]:
    """
    Extract key metrics from analysis results

    Args:
        analysis_results: Dictionary containing analysis results

    Returns:
        Dictionary with key metrics
    """
    brand_perf = analysis_results["brand_performance"]
    media_stats = analysis_results["media_stats"]

    return {
        "total_products": analysis_results["total_products"],
        "missing_prices": analysis_results["missing_prices"],
        "avg_rating": analysis_results["rating_distribution"]["mean"],
        "total_brands": brand_perf["overall_metrics"]["total_brands"],
        "brands_analyzed": brand_perf["overall_metrics"]["brands_analyzed"],
        "mean_reviews_per_brand": brand_perf["overall_metrics"]["review_statistics"]["mean_reviews_per_brand"],
        "products_with_images_pct": media_stats["image_metrics"]["products_with_images"]["percentage"],
        "avg_images_per_product": media_stats["image_metrics"]["image_distribution"]["mean"],
        "products_with_videos_pct": media_stats["video_metrics"]["products_with_videos"]["percentage"],
    }


def analyze_category(category: str) -> dict[str, Any]:
    """
    Analyze a single category and return key metrics
    """
    logger.info(f"Analyzing category: {category}")

    try:
        df = load_amazon_data_to_df(category)
        df["price"] = pd.to_numeric(df["price"], errors="coerce")

        results = {
            "category": category,
            "total_products": len(df),
            "missing_prices": int(df["price"].isna().sum()),
            "rating_distribution": df["average_rating"].describe().to_dict(),
            "media_stats": analyze_media_presence(df),
            "brand_performance": analyze_brand_performance(df, min_reviews=50),
        }

        return extract_key_metrics(results)

    except Exception as e:
        logger.error(f"Error analyzing {category}: {str(e)}")
        raise  # Re-raise exception instead of returning None


def analyze_all_categories(categories: list[str]) -> pd.DataFrame:
    """
    Analyze all categories and return results as DataFrame

    Args:
        categories: List of category names

    Returns:
        DataFrame containing analysis results
    """
    results = []

    for category in categories:
        metrics = analyze_category(category)
        if metrics:
            results.append(metrics)

    return pd.DataFrame(results)


def main() -> None:
    """Main function to run analysis and save results"""
    categories = [
        "All_Beauty",
        "Amazon_Fashion",
        "Appliances",
        "Arts_Crafts_and_Sewing",
        "Automotive",
        "Baby_Products",
    ]

    # Run analysis
    results_df = analyze_all_categories(categories)

    # Save results
    output_path = Path("analysis_results.csv")
    results_df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

    # Display summary
    print("\nAnalysis Summary:")
    print(results_df.to_string())
