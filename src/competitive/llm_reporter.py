import logging
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print(
        "Warning: OpenAI package not installed. LLM features will use fallback analysis."
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMReporter:
    """LLM-powered competitive positioning report generator with OpenAI integration"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.use_openai = OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY")

        if self.use_openai:
            openai.api_key = os.getenv("OPENAI_API_KEY")
            logger.info(f"OpenAI LLM integration enabled with model: {model}")
        else:
            logger.info("Using fallback structured analysis (OpenAI not configured)")

    def generate_positioning_report(self, analysis_data: Dict) -> Dict:
        """Generate competitive positioning report using OpenAI or fallback analysis"""
        try:
            logger.info("Generating competitive positioning report")

            if self.use_openai:
                return self._generate_openai_report(analysis_data)
            else:
                return self._generate_fallback_report(analysis_data)

        except Exception as e:
            logger.error(f"Error generating positioning report: {str(e)}")
            return {"error": str(e)}

    def _generate_openai_report(self, analysis_data: Dict) -> Dict:
        """Generate report using OpenAI API"""
        try:
            # Extract key data
            main_product = analysis_data.get("main_product", {})
            competitors = analysis_data.get("competitors", [])
            price_analysis = analysis_data.get("price_analysis", {})
            bsr_analysis = analysis_data.get("bsr_analysis", {})
            rating_analysis = analysis_data.get("rating_analysis", {})
            feature_analysis = analysis_data.get("feature_analysis", {})
            competitive_summary = analysis_data.get("competitive_summary", {})

            # Create comprehensive prompt for OpenAI
            prompt = self._create_analysis_prompt(analysis_data)

            # Call OpenAI API
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert e-commerce competitive analyst. Analyze the provided Amazon product data and generate comprehensive business insights.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=4000,
            )

            # Parse OpenAI response
            llm_analysis = response.choices[0].message.content

            # Combine structured data with LLM insights
            report = {
                "executive_summary": self._extract_executive_summary(
                    llm_analysis, competitive_summary, main_product
                ),
                "competitive_positioning": self._analyze_competitive_positioning(
                    price_analysis, rating_analysis, bsr_analysis
                ),
                "strengths_weaknesses": self._extract_swot_analysis(
                    llm_analysis, analysis_data
                ),
                "feature_differentiation": self._analyze_feature_differentiation(
                    feature_analysis
                ),
                "strategic_recommendations": self._extract_recommendations(
                    llm_analysis, analysis_data
                ),
                "market_insights": self._extract_market_insights(
                    llm_analysis, analysis_data
                ),
                "llm_detailed_analysis": llm_analysis,
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "model_used": self.model,
                    "llm_enabled": True,
                    "analysis_confidence": competitive_summary.get(
                        "analysis_confidence", "medium"
                    ),
                    "data_points_analyzed": len(competitors) + 1,
                },
            }

            return report

        except Exception as e:
            logger.error(f"Error generating OpenAI report: {str(e)}")
            # Fallback to structured analysis
            return self._generate_fallback_report(analysis_data)

    def _generate_fallback_report(self, analysis_data: Dict) -> Dict:
        """Generate report using structured analysis (fallback)"""
        # Extract key data
        main_product = analysis_data.get("main_product", {})
        competitors = analysis_data.get("competitors", [])
        price_analysis = analysis_data.get("price_analysis", {})
        bsr_analysis = analysis_data.get("bsr_analysis", {})
        rating_analysis = analysis_data.get("rating_analysis", {})
        feature_analysis = analysis_data.get("feature_analysis", {})
        competitive_summary = analysis_data.get("competitive_summary", {})

        # Generate structured report
        report = {
            "executive_summary": self._generate_executive_summary(
                competitive_summary, main_product
            ),
            "competitive_positioning": self._analyze_competitive_positioning(
                price_analysis, rating_analysis, bsr_analysis
            ),
            "strengths_weaknesses": self._identify_strengths_weaknesses(analysis_data),
            "feature_differentiation": self._analyze_feature_differentiation(
                feature_analysis
            ),
            "strategic_recommendations": self._generate_recommendations(analysis_data),
            "market_insights": self._generate_market_insights(analysis_data),
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "model_used": "structured_analysis",
                "llm_enabled": False,
                "analysis_confidence": competitive_summary.get(
                    "analysis_confidence", "medium"
                ),
                "data_points_analyzed": len(competitors) + 1,
            },
        }

        return report

    def _create_analysis_prompt(self, analysis_data: Dict) -> str:
        """Create comprehensive analysis prompt for OpenAI"""
        main_product = analysis_data.get("main_product", {})
        competitors = analysis_data.get("competitors", [])
        price_analysis = analysis_data.get("price_analysis", {})
        rating_analysis = analysis_data.get("rating_analysis", {})
        feature_analysis = analysis_data.get("feature_analysis", {})

        prompt = f"""
        Analyze the following Amazon product competitive landscape:

        MAIN PRODUCT:
        - ASIN: {main_product.get('asin')}
        - Title: {main_product.get('title')}
        - Price: ${main_product.get('price', 'N/A')}
        - Rating: {main_product.get('rating', 'N/A')}/5.0
        - Reviews: {main_product.get('review_count', 'N/A')}
        - Features: {main_product.get('bullet_points', [])}

        COMPETITORS ({len(competitors)} products):
        """

        for i, comp in enumerate(competitors[:5], 1):  # Limit to top 5 for prompt size
            prompt += f"""
        {i}. {comp.get('title', 'Unknown')[:50]}...
           - ASIN: {comp.get('asin')}
           - Price: ${comp.get('price', 'N/A')}
           - Rating: {comp.get('rating', 'N/A')}/5.0
           - Reviews: {comp.get('review_count', 'N/A')}
           - Features: {comp.get('bullet_points', [])[:3]}
        """

        prompt += f"""

        PRICE ANALYSIS:
        - Main product position: {price_analysis.get('price_position', 'unknown')}
        - Market average: ${price_analysis.get('market_price_range', {}).get('average', 'N/A')}
        - Price advantage: {price_analysis.get('price_advantage', 'N/A')}

        FEATURE ANALYSIS:
        - Unique features: {feature_analysis.get('unique_to_main', {})}
        - Missing features: {feature_analysis.get('missing_from_main', {})}

        Please provide a comprehensive competitive analysis including:
        1. Executive summary of market position
        2. SWOT analysis (Strengths, Weaknesses, Opportunities, Threats)
        3. Key competitive advantages and disadvantages
        4. Strategic recommendations for improvement
        5. Market insights and trends
        6. Feature differentiation assessment

        Focus on actionable business insights for the main product seller.
        """

        return prompt

    def _extract_executive_summary(
        self, llm_analysis: str, competitive_summary: Dict, main_product: Dict
    ) -> str:
        """Extract executive summary from LLM analysis or use fallback"""
        try:
            # Try to extract executive summary section from LLM response
            lines = llm_analysis.split("\n")
            summary_started = False
            summary_lines = []

            for line in lines:
                if "executive" in line.lower() and "summary" in line.lower():
                    summary_started = True
                    continue
                elif summary_started and ("2." in line or "swot" in line.lower()):
                    break
                elif summary_started and line.strip():
                    summary_lines.append(line.strip())

            if summary_lines:
                return " ".join(summary_lines)
            else:
                # Fallback to structured summary
                return self._generate_executive_summary(
                    competitive_summary, main_product
                )

        except Exception as e:
            logger.error(f"Error extracting executive summary: {str(e)}")
            return self._generate_executive_summary(competitive_summary, main_product)

    def _extract_swot_analysis(self, llm_analysis: str, analysis_data: Dict) -> Dict:
        """Extract SWOT analysis from LLM response or use fallback"""
        try:
            # Try to parse SWOT from LLM response
            swot = {
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "threats": [],
            }

            lines = llm_analysis.lower().split("\n")
            current_section = None

            for line in lines:
                line = line.strip()
                if "strengths" in line:
                    current_section = "strengths"
                elif "weaknesses" in line:
                    current_section = "weaknesses"
                elif "opportunities" in line:
                    current_section = "opportunities"
                elif "threats" in line:
                    current_section = "threats"
                elif current_section and line and line.startswith("-"):
                    swot[current_section].append(line[1:].strip())

            # If no SWOT found, use fallback
            if not any(swot.values()):
                return self._identify_strengths_weaknesses(analysis_data)

            return swot

        except Exception as e:
            logger.error(f"Error extracting SWOT: {str(e)}")
            return self._identify_strengths_weaknesses(analysis_data)

    def _extract_recommendations(
        self, llm_analysis: str, analysis_data: Dict
    ) -> List[Dict]:
        """Extract recommendations from LLM response or use fallback"""
        try:
            recommendations = []
            lines = llm_analysis.split("\n")
            in_recommendations = False

            for line in lines:
                line = line.strip()
                if "recommendation" in line.lower() or "strategic" in line.lower():
                    in_recommendations = True
                    continue
                elif (
                    in_recommendations
                    and line
                    and (line.startswith("-") or line.startswith("•"))
                ):
                    recommendations.append(
                        {
                            "category": "strategic",
                            "priority": "medium",
                            "action": line[1:].strip(),
                            "rationale": "Based on competitive analysis",
                            "expected_impact": "Market position improvement",
                        }
                    )

            # If no recommendations found, use fallback
            if not recommendations:
                return self._generate_recommendations(analysis_data)

            return recommendations

        except Exception as e:
            logger.error(f"Error extracting recommendations: {str(e)}")
            return self._generate_recommendations(analysis_data)

    def _extract_market_insights(self, llm_analysis: str, analysis_data: Dict) -> Dict:
        """Extract market insights from LLM response or use fallback"""
        try:
            insights = {
                "trends": [],
                "market_dynamics": {},
                "competitive_landscape": {},
            }

            lines = llm_analysis.split("\n")
            in_insights = False

            for line in lines:
                line = line.strip()
                if "market" in line.lower() and (
                    "insight" in line.lower() or "trend" in line.lower()
                ):
                    in_insights = True
                    continue
                elif (
                    in_insights
                    and line
                    and (line.startswith("-") or line.startswith("•"))
                ):
                    insights["trends"].append(line[1:].strip())

            # Add fallback insights
            fallback_insights = self._generate_market_insights(analysis_data)
            insights.update(fallback_insights)

            return insights

        except Exception as e:
            logger.error(f"Error extracting market insights: {str(e)}")
            return self._generate_market_insights(analysis_data)

    def _generate_executive_summary(
        self, competitive_summary: Dict, main_product: Dict
    ) -> str:
        """Generate executive summary"""
        try:
            scores = competitive_summary.get("competitive_scores", {})
            position = competitive_summary.get("position_summary", {})

            overall_score = scores.get("overall_competitiveness", 0)
            product_title = main_product.get("title", "Unknown Product")[:50]

            if overall_score >= 80:
                performance = "exceptionally strong"
            elif overall_score >= 60:
                performance = "competitive"
            elif overall_score >= 40:
                performance = "moderate"
            else:
                performance = "challenging"

            summary = f"""
            {product_title} shows {performance} market positioning with an overall competitiveness score of {overall_score:.1f}/100.
            
            The product is positioned as {position.get('price_position', 'unknown')} in pricing, 
            {position.get('quality_position', 'unknown')} in quality metrics, and 
            {position.get('popularity_position', 'unknown')} in market popularity.
            
            Key competitive stance: {position.get('overall_position', 'unknown')} market position 
            among {competitive_summary.get('total_competitors', 0)} analyzed competitors.
            """.strip()

            return summary

        except Exception as e:
            logger.error(f"Error generating executive summary: {str(e)}")
            return "Executive summary generation failed"

    def _analyze_competitive_positioning(
        self, price_analysis: Dict, rating_analysis: Dict, bsr_analysis: Dict
    ) -> Dict:
        """Analyze competitive positioning across dimensions"""
        positioning = {
            "price_positioning": {
                "position": price_analysis.get("price_position", "unknown"),
                "advantage": price_analysis.get("price_advantage", False),
                "market_context": f"Positioned in {price_analysis.get('price_position', 'unknown')} price tier",
            },
            "quality_positioning": {
                "rating": rating_analysis.get("main_product", {}).get("rating"),
                "position": rating_analysis.get("rating_statistics", {}).get(
                    "main_product_position", "unknown"
                ),
                "advantage": rating_analysis.get("quality_advantage", False),
            },
            "popularity_positioning": {},
            "recommendations": [],
        }

        # Analyze BSR positioning
        if bsr_analysis and not bsr_analysis.get("error"):
            best_category = None
            best_position = None

            for category, data in bsr_analysis.items():
                if isinstance(data, dict) and data.get("position") == "best":
                    best_category = category
                    best_position = data.get("main_product_rank")
                    break

            positioning["popularity_positioning"] = {
                "best_category": best_category,
                "best_rank": best_position,
                "overall_performance": "strong" if best_category else "moderate",
            }

        # Generate positioning recommendations
        if price_analysis.get("price_position") == "highest":
            positioning["recommendations"].append(
                "Consider price optimization to improve competitiveness"
            )

        if rating_analysis.get("quality_advantage") == False:
            positioning["recommendations"].append(
                "Focus on product quality improvements and customer satisfaction"
            )

        return positioning

    def _identify_strengths_weaknesses(self, analysis_data: Dict) -> Dict:
        """Identify competitive strengths and weaknesses"""
        strengths = []
        weaknesses = []
        opportunities = []
        threats = []

        # Analyze price
        price_analysis = analysis_data.get("price_analysis", {})
        if price_analysis.get("price_advantage"):
            strengths.append("Competitive pricing advantage")
        elif price_analysis.get("price_position") == "highest":
            weaknesses.append("Premium pricing may limit market reach")

        # Analyze quality
        rating_analysis = analysis_data.get("rating_analysis", {})
        if rating_analysis.get("quality_advantage"):
            strengths.append("Superior customer satisfaction ratings")
        else:
            opportunities.append("Potential for quality improvement initiatives")

        # Analyze features
        feature_analysis = analysis_data.get("feature_analysis", {})
        unique_features = feature_analysis.get("unique_to_main", {})
        if any(features for features in unique_features.values()):
            strengths.append("Unique product features not found in competitors")

        missing_features = feature_analysis.get("missing_from_main", {})
        if any(features for features in missing_features.values()):
            opportunities.append(
                "Feature gaps present opportunities for product enhancement"
            )

        # Analyze market position
        competitive_summary = analysis_data.get("competitive_summary", {})
        scores = competitive_summary.get("competitive_scores", {})

        if scores.get("overall_competitiveness", 0) > 70:
            strengths.append("Strong overall market positioning")
        elif scores.get("overall_competitiveness", 0) < 40:
            threats.append("Weak competitive position requires strategic intervention")

        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "opportunities": opportunities,
            "threats": threats,
        }

    def _analyze_feature_differentiation(self, feature_analysis: Dict) -> Dict:
        """Analyze product feature differentiation"""
        try:
            unique_features = feature_analysis.get("unique_to_main", {})
            common_features = feature_analysis.get("common_features", {})
            missing_features = feature_analysis.get("missing_from_main", {})

            # Calculate differentiation score
            total_unique = sum(len(features) for features in unique_features.values())
            total_common = sum(len(features) for features in common_features.values())
            total_missing = sum(len(features) for features in missing_features.values())

            differentiation_score = 0
            if total_unique + total_common + total_missing > 0:
                differentiation_score = (
                    (total_unique * 2 + total_common - total_missing)
                    / (total_unique + total_common + total_missing)
                    * 50
                )
                differentiation_score = max(0, min(100, differentiation_score))

            return {
                "differentiation_score": round(differentiation_score, 1),
                "unique_features_count": total_unique,
                "common_features_count": total_common,
                "missing_features_count": total_missing,
                "differentiation_level": (
                    "high"
                    if differentiation_score > 70
                    else "moderate" if differentiation_score > 40 else "low"
                ),
                "key_differentiators": unique_features,
                "feature_gaps": missing_features,
            }

        except Exception as e:
            logger.error(f"Error analyzing feature differentiation: {str(e)}")
            return {"error": str(e)}

    def _generate_recommendations(self, analysis_data: Dict) -> List[Dict]:
        """Generate strategic recommendations"""
        recommendations = []

        try:
            price_analysis = analysis_data.get("price_analysis", {})
            rating_analysis = analysis_data.get("rating_analysis", {})
            feature_analysis = analysis_data.get("feature_analysis", {})
            competitive_summary = analysis_data.get("competitive_summary", {})

            # Price recommendations
            if price_analysis.get("price_position") == "highest":
                recommendations.append(
                    {
                        "category": "pricing",
                        "priority": "high",
                        "action": "Consider price adjustment",
                        "rationale": f"Current price is {price_analysis.get('cheaper_competitors', 0)} competitors are priced lower",
                        "expected_impact": "Increased market competitiveness",
                    }
                )

            # Quality recommendations
            if not rating_analysis.get("quality_advantage"):
                recommendations.append(
                    {
                        "category": "quality",
                        "priority": "medium",
                        "action": "Improve product quality and customer experience",
                        "rationale": "Competitor ratings suggest room for improvement",
                        "expected_impact": "Enhanced customer satisfaction and reviews",
                    }
                )

            # Feature recommendations
            missing_features = feature_analysis.get("missing_from_main", {})
            if any(features for features in missing_features.values()):
                recommendations.append(
                    {
                        "category": "features",
                        "priority": "medium",
                        "action": "Evaluate adding missing features",
                        "rationale": "Competitors offer features not present in main product",
                        "expected_impact": "Improved feature parity and customer appeal",
                    }
                )

            # Market position recommendations
            overall_score = competitive_summary.get("competitive_scores", {}).get(
                "overall_competitiveness", 0
            )
            if overall_score < 50:
                recommendations.append(
                    {
                        "category": "strategy",
                        "priority": "high",
                        "action": "Comprehensive competitive strategy review",
                        "rationale": f"Overall competitiveness score of {overall_score:.1f} indicates strategic challenges",
                        "expected_impact": "Improved market positioning and competitive advantage",
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []

    def _generate_market_insights(self, analysis_data: Dict) -> Dict:
        """Generate market insights"""
        try:
            insights = {
                "market_dynamics": {},
                "competitive_landscape": {},
                "trends": {},
            }

            # Market dynamics
            price_analysis = analysis_data.get("price_analysis", {})
            market_range = price_analysis.get("market_price_range", {})

            if market_range:
                price_spread = market_range.get("spread", 0)
                avg_price = market_range.get("average", 0)

                insights["market_dynamics"] = {
                    "price_volatility": (
                        "high"
                        if price_spread > avg_price * 0.5
                        else "moderate" if price_spread > avg_price * 0.2 else "low"
                    ),
                    "market_maturity": (
                        "fragmented"
                        if price_spread > avg_price * 0.3
                        else "consolidated"
                    ),
                    "price_competition_intensity": (
                        "high"
                        if len(analysis_data.get("competitors", [])) > 5
                        else "moderate"
                    ),
                }

            # Competitive landscape
            competitive_summary = analysis_data.get("competitive_summary", {})
            scores = competitive_summary.get("competitive_scores", {})

            insights["competitive_landscape"] = {
                "market_leadership": scores.get("popularity_competitiveness", 0) > 70,
                "quality_differentiation": scores.get("quality_competitiveness", 0)
                > 80,
                "price_leadership": scores.get("price_competitiveness", 0) > 80,
                "overall_market_position": competitive_summary.get(
                    "position_summary", {}
                ).get("overall_position", "unknown"),
            }

            return insights

        except Exception as e:
            logger.error(f"Error generating market insights: {str(e)}")
            return {"error": str(e)}
