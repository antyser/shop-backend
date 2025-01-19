import asyncio

import streamlit as st
from agents.product_research_agent import ProductReviewAnalysis, analyze_product
from logfire_init import init_logfire
from loguru import logger


def display_analysis(analysis: ProductReviewAnalysis) -> None:
    """Display the product analysis in a structured format

    Args:
        analysis: Product review analysis results
    """
    # Summary section
    st.header("Product Analysis")
    st.write(analysis.summary)

    # Rating and Price-Value
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Overall Rating", f"{analysis.overall_rating}/10")
    with col2:
        st.metric("Price-Value Ratio", analysis.price_value_ratio)

    # Features
    st.subheader("Product Features")
    for feature in analysis.features:
        st.markdown(f"📋 {feature}")

    # Evaluation Criteria
    st.subheader("Evaluation Criteria")
    for criterion in analysis.evaluation_criteria:
        st.markdown(f"- {criterion}")

    # Pros and Cons
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Pros")
        for pro in analysis.pros:
            st.markdown(f"✅ {pro}")

    with col2:
        st.subheader("Cons")
        for con in analysis.cons:
            st.markdown(f"❌ {con}")

    # Best For
    st.subheader("Best For")
    for use_case in analysis.best_for:
        st.markdown(f"🎯 {use_case}")

    # Alternatives
    st.subheader("Alternative Products")
    for alt in analysis.alternatives:
        st.markdown(f"🔄 {alt}")


async def get_product_analysis(query: str) -> ProductReviewAnalysis | None:
    """Get product analysis with error handling

    Args:
        query: Product name or URL to analyze

    Returns:
        Analysis results or None if error occurs
    """
    try:
        return await analyze_product(query)
    except Exception as e:
        logger.error(f"Error analyzing product: {str(e)}")
        st.error("Failed to analyze product. Please try again.")
        return None


def main() -> None:
    init_logfire()
    """Main Streamlit application"""
    st.set_page_config(page_title="Product Research Assistant", page_icon="🔍", layout="wide")

    # Initialize event loop in session state if not exists
    if "event_loop" not in st.session_state:
        st.session_state.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(st.session_state.event_loop)

    st.title("🔍 Product Research Assistant")
    st.write("Enter a product name or Amazon URL to get comprehensive " "analysis based on features, reviews, and market data.")

    # Input section
    query = st.text_input("Product Name or Amazon URL", placeholder="e.g., iPhone 15 Pro or https://www.amazon.com/dp/...")

    if st.button("Analyze Product") and query:
        with st.spinner("Analyzing product... This may take a minute..."):
            # Use the persistent event loop
            analysis = st.session_state.event_loop.run_until_complete(get_product_analysis(query))
            if analysis:
                display_analysis(analysis)

    # Footer
    st.markdown("---")
    st.markdown("Powered by AI - Analyzes product reviews " "to provide comprehensive insights")


if __name__ == "__main__":
    main()
