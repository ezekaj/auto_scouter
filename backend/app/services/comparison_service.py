"""
Vehicle Comparison Service

This module provides comprehensive vehicle comparison functionality including:
- Creating and managing comparisons
- Analyzing vehicle differences
- Generating comparison insights
- Scoring and recommendations
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.comparison import (
    VehicleComparison, VehicleComparisonItem, ComparisonTemplate,
    ComparisonShare, ComparisonView
)
from app.models.automotive import VehicleListing
from app.models.scout import User
from app.schemas.comparison import (
    VehicleComparisonCreate, VehicleComparisonUpdate,
    ComparisonAnalysis, ComparisonInsights, ComparisonRecommendation
)

logger = logging.getLogger(__name__)


class ComparisonService:
    """Service for vehicle comparison operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_comparison(self, user_id: int, comparison_data: VehicleComparisonCreate) -> VehicleComparison:
        """Create a new vehicle comparison"""
        try:
            # Create the comparison
            comparison = VehicleComparison(
                user_id=user_id,
                name=comparison_data.name,
                description=comparison_data.description,
                comparison_criteria=comparison_data.comparison_criteria,
                is_public=comparison_data.is_public
            )
            
            self.db.add(comparison)
            self.db.flush()  # Get the ID
            
            # Add vehicles to comparison
            for i, vehicle_id in enumerate(comparison_data.vehicle_ids):
                vehicle = self.db.query(VehicleListing).filter(VehicleListing.id == vehicle_id).first()
                if vehicle:
                    comparison_item = VehicleComparisonItem(
                        comparison_id=comparison.id,
                        vehicle_id=vehicle_id,
                        position=i
                    )
                    self.db.add(comparison_item)
            
            self.db.commit()
            self.db.refresh(comparison)
            
            # Calculate initial scores
            self._calculate_comparison_scores(comparison.id)
            
            logger.info(f"Created comparison {comparison.id} for user {user_id}")
            return comparison
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create comparison: {str(e)}")
            raise
    
    def get_user_comparisons(self, user_id: int, page: int = 1, limit: int = 20) -> Tuple[List[VehicleComparison], int]:
        """Get user's comparisons with pagination"""
        query = self.db.query(VehicleComparison).filter(
            VehicleComparison.user_id == user_id
        ).order_by(desc(VehicleComparison.updated_at))
        
        total = query.count()
        comparisons = query.offset((page - 1) * limit).limit(limit).all()
        
        return comparisons, total
    
    def get_comparison_by_id(self, comparison_id: int, user_id: Optional[int] = None) -> Optional[VehicleComparison]:
        """Get comparison by ID with optional user check"""
        query = self.db.query(VehicleComparison).filter(VehicleComparison.id == comparison_id)
        
        if user_id:
            query = query.filter(
                or_(
                    VehicleComparison.user_id == user_id,
                    VehicleComparison.is_public == True
                )
            )
        
        comparison = query.first()
        
        if comparison:
            # Update last accessed time
            comparison.last_accessed = datetime.utcnow()
            self.db.commit()
        
        return comparison
    
    def add_vehicle_to_comparison(self, comparison_id: int, vehicle_id: int, user_id: int) -> VehicleComparisonItem:
        """Add a vehicle to an existing comparison"""
        # Check if user owns the comparison
        comparison = self.db.query(VehicleComparison).filter(
            and_(
                VehicleComparison.id == comparison_id,
                VehicleComparison.user_id == user_id
            )
        ).first()
        
        if not comparison:
            raise ValueError("Comparison not found or access denied")
        
        # Check if vehicle exists
        vehicle = self.db.query(VehicleListing).filter(VehicleListing.id == vehicle_id).first()
        if not vehicle:
            raise ValueError("Vehicle not found")
        
        # Check if vehicle is already in comparison
        existing_item = self.db.query(VehicleComparisonItem).filter(
            and_(
                VehicleComparisonItem.comparison_id == comparison_id,
                VehicleComparisonItem.vehicle_id == vehicle_id
            )
        ).first()
        
        if existing_item:
            raise ValueError("Vehicle already in comparison")
        
        # Get next position
        max_position = self.db.query(func.max(VehicleComparisonItem.position)).filter(
            VehicleComparisonItem.comparison_id == comparison_id
        ).scalar() or -1
        
        # Create comparison item
        comparison_item = VehicleComparisonItem(
            comparison_id=comparison_id,
            vehicle_id=vehicle_id,
            position=max_position + 1
        )
        
        self.db.add(comparison_item)
        self.db.commit()
        self.db.refresh(comparison_item)
        
        # Recalculate scores
        self._calculate_comparison_scores(comparison_id)
        
        return comparison_item
    
    def remove_vehicle_from_comparison(self, comparison_id: int, vehicle_id: int, user_id: int) -> bool:
        """Remove a vehicle from comparison"""
        # Check ownership
        comparison = self.db.query(VehicleComparison).filter(
            and_(
                VehicleComparison.id == comparison_id,
                VehicleComparison.user_id == user_id
            )
        ).first()
        
        if not comparison:
            return False
        
        # Remove the item
        item = self.db.query(VehicleComparisonItem).filter(
            and_(
                VehicleComparisonItem.comparison_id == comparison_id,
                VehicleComparisonItem.vehicle_id == vehicle_id
            )
        ).first()
        
        if item:
            self.db.delete(item)
            self.db.commit()
            
            # Recalculate scores
            self._calculate_comparison_scores(comparison_id)
            return True
        
        return False
    
    def analyze_comparison(self, comparison_id: int) -> ComparisonAnalysis:
        """Analyze a comparison and provide insights"""
        comparison = self.db.query(VehicleComparison).filter(
            VehicleComparison.id == comparison_id
        ).first()
        
        if not comparison:
            raise ValueError("Comparison not found")
        
        # Get all vehicles in comparison
        items = self.db.query(VehicleComparisonItem).filter(
            VehicleComparisonItem.comparison_id == comparison_id
        ).all()
        
        vehicles = [item.vehicle for item in items]
        
        if not vehicles:
            return ComparisonAnalysis()
        
        # Calculate analysis
        analysis = ComparisonAnalysis()
        
        # Find best value (price vs features)
        best_value_vehicle = self._find_best_value_vehicle(vehicles)
        if best_value_vehicle:
            analysis.best_value = {
                'vehicle_id': best_value_vehicle.id,
                'make': best_value_vehicle.make,
                'model': best_value_vehicle.model,
                'price': best_value_vehicle.price,
                'value_score': self._calculate_value_score(best_value_vehicle, vehicles)
            }
        
        # Find best performance
        best_performance_vehicle = self._find_best_performance_vehicle(vehicles)
        if best_performance_vehicle:
            analysis.best_performance = {
                'vehicle_id': best_performance_vehicle.id,
                'make': best_performance_vehicle.make,
                'model': best_performance_vehicle.model,
                'engine_power_hp': best_performance_vehicle.engine_power_hp,
                'performance_score': self._calculate_performance_score(best_performance_vehicle)
            }
        
        # Find best condition
        best_condition_vehicle = self._find_best_condition_vehicle(vehicles)
        if best_condition_vehicle:
            analysis.best_condition = {
                'vehicle_id': best_condition_vehicle.id,
                'make': best_condition_vehicle.make,
                'model': best_condition_vehicle.model,
                'year': best_condition_vehicle.year,
                'mileage': best_condition_vehicle.mileage,
                'condition_score': self._calculate_condition_score(best_condition_vehicle)
            }
        
        # Calculate price range
        prices = [v.price for v in vehicles if v.price]
        if prices:
            analysis.price_range = {
                'min': min(prices),
                'max': max(prices),
                'average': sum(prices) / len(prices),
                'median': sorted(prices)[len(prices) // 2]
            }
        
        # Calculate average specs
        analysis.average_specs = self._calculate_average_specs(vehicles)
        
        # Generate recommendations
        analysis.recommendations = self._generate_recommendations(vehicles, analysis)
        
        return analysis
    
    def _calculate_comparison_scores(self, comparison_id: int):
        """Calculate scores for all vehicles in a comparison"""
        items = self.db.query(VehicleComparisonItem).filter(
            VehicleComparisonItem.comparison_id == comparison_id
        ).all()
        
        vehicles = [item.vehicle for item in items]
        
        for item in items:
            vehicle = item.vehicle
            
            # Calculate various scores
            item.price_score = self._calculate_price_competitiveness(vehicle, vehicles)
            item.feature_score = self._calculate_feature_completeness(vehicle)
            item.condition_score = self._calculate_condition_score(vehicle)
            
            # Overall score (weighted average)
            item.overall_score = (
                item.price_score * 0.4 +
                item.feature_score * 0.3 +
                item.condition_score * 0.3
            )
        
        self.db.commit()
    
    def _calculate_price_competitiveness(self, vehicle: VehicleListing, all_vehicles: List[VehicleListing]) -> float:
        """Calculate how competitive a vehicle's price is (lower is better)"""
        if not vehicle.price:
            return 0.5
        
        prices = [v.price for v in all_vehicles if v.price]
        if len(prices) <= 1:
            return 0.5
        
        # Normalize price (lower price = higher score)
        min_price = min(prices)
        max_price = max(prices)
        
        if max_price == min_price:
            return 0.5
        
        # Invert the score so lower price = higher score
        score = 1.0 - (vehicle.price - min_price) / (max_price - min_price)
        return max(0.0, min(1.0, score))
    
    def _calculate_feature_completeness(self, vehicle: VehicleListing) -> float:
        """Calculate how complete the vehicle's feature set is"""
        features = [
            vehicle.engine_power_hp,
            vehicle.engine_displacement,
            vehicle.fuel_type,
            vehicle.transmission,
            vehicle.body_type,
            vehicle.doors,
            vehicle.seats,
            vehicle.color_exterior
        ]
        
        completed_features = sum(1 for f in features if f is not None)
        return completed_features / len(features)
    
    def _calculate_condition_score(self, vehicle: VehicleListing) -> float:
        """Calculate vehicle condition score"""
        score = 0.5  # Base score
        
        # Year factor (newer is better)
        if vehicle.year:
            current_year = datetime.now().year
            age = current_year - vehicle.year
            if age <= 2:
                score += 0.3
            elif age <= 5:
                score += 0.2
            elif age <= 10:
                score += 0.1
        
        # Mileage factor (lower is better)
        if vehicle.mileage:
            if vehicle.mileage < 50000:
                score += 0.2
            elif vehicle.mileage < 100000:
                score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _find_best_value_vehicle(self, vehicles: List[VehicleListing]) -> Optional[VehicleListing]:
        """Find the vehicle with the best value proposition"""
        if not vehicles:
            return None
        
        best_vehicle = None
        best_score = -1
        
        for vehicle in vehicles:
            score = self._calculate_value_score(vehicle, vehicles)
            if score > best_score:
                best_score = score
                best_vehicle = vehicle
        
        return best_vehicle
    
    def _calculate_value_score(self, vehicle: VehicleListing, all_vehicles: List[VehicleListing]) -> float:
        """Calculate value score (features per dollar)"""
        if not vehicle.price:
            return 0.0
        
        feature_score = self._calculate_feature_completeness(vehicle)
        condition_score = self._calculate_condition_score(vehicle)
        price_competitiveness = self._calculate_price_competitiveness(vehicle, all_vehicles)
        
        # Combine scores with weights
        value_score = (feature_score * 0.3 + condition_score * 0.3 + price_competitiveness * 0.4)
        return value_score
    
    def _find_best_performance_vehicle(self, vehicles: List[VehicleListing]) -> Optional[VehicleListing]:
        """Find the vehicle with the best performance"""
        performance_vehicles = [v for v in vehicles if v.engine_power_hp]
        if not performance_vehicles:
            return None
        
        return max(performance_vehicles, key=lambda v: v.engine_power_hp or 0)
    
    def _calculate_performance_score(self, vehicle: VehicleListing) -> float:
        """Calculate performance score"""
        if not vehicle.engine_power_hp:
            return 0.0
        
        # Normalize based on typical ranges
        # 100hp = 0.2, 200hp = 0.5, 400hp = 1.0
        normalized_hp = min(vehicle.engine_power_hp / 400.0, 1.0)
        return normalized_hp
    
    def _find_best_condition_vehicle(self, vehicles: List[VehicleListing]) -> Optional[VehicleListing]:
        """Find the vehicle in the best condition"""
        if not vehicles:
            return None
        
        best_vehicle = None
        best_score = -1
        
        for vehicle in vehicles:
            score = self._calculate_condition_score(vehicle)
            if score > best_score:
                best_score = score
                best_vehicle = vehicle
        
        return best_vehicle
    
    def _calculate_average_specs(self, vehicles: List[VehicleListing]) -> Dict[str, Any]:
        """Calculate average specifications across vehicles"""
        if not vehicles:
            return {}
        
        specs = {}
        
        # Average price
        prices = [v.price for v in vehicles if v.price]
        if prices:
            specs['average_price'] = sum(prices) / len(prices)
        
        # Average year
        years = [v.year for v in vehicles if v.year]
        if years:
            specs['average_year'] = sum(years) / len(years)
        
        # Average mileage
        mileages = [v.mileage for v in vehicles if v.mileage]
        if mileages:
            specs['average_mileage'] = sum(mileages) / len(mileages)
        
        # Average power
        powers = [v.engine_power_hp for v in vehicles if v.engine_power_hp]
        if powers:
            specs['average_power_hp'] = sum(powers) / len(powers)
        
        return specs
    
    def _generate_recommendations(self, vehicles: List[VehicleListing], analysis: ComparisonAnalysis) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if analysis.best_value:
            recommendations.append(
                f"For best value, consider the {analysis.best_value['make']} {analysis.best_value['model']} "
                f"at €{analysis.best_value['price']:,.0f}"
            )
        
        if analysis.best_performance:
            recommendations.append(
                f"For best performance, the {analysis.best_performance['make']} {analysis.best_performance['model']} "
                f"offers {analysis.best_performance['engine_power_hp']}hp"
            )
        
        if analysis.price_range:
            price_diff = analysis.price_range['max'] - analysis.price_range['min']
            if price_diff > 10000:
                recommendations.append(
                    f"Price range is quite wide (€{price_diff:,.0f} difference). "
                    "Consider if the higher-priced options offer proportional value."
                )
        
        return recommendations
