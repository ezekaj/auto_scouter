"""
Price Tracking Service

This module provides comprehensive price tracking functionality including:
- Recording price changes over time
- Analyzing price trends and patterns
- Generating price alerts and notifications
- Market position analysis
- Price prediction and forecasting
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, asc
from statistics import mean, median

from app.models.automotive import VehicleListing, PriceHistory
from app.models.scout import User
from app.models.notifications import Notification, NotificationType

logger = logging.getLogger(__name__)


class PriceTrackingService:
    """Service for vehicle price tracking and analysis"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_price_change(self, vehicle_id: int, new_price: float, 
                          source_website: Optional[str] = None,
                          source_url: Optional[str] = None) -> PriceHistory:
        """Record a new price for a vehicle"""
        try:
            vehicle = self.db.query(VehicleListing).filter(VehicleListing.id == vehicle_id).first()
            if not vehicle:
                raise ValueError(f"Vehicle {vehicle_id} not found")
            
            # Get the most recent price
            latest_price = self.db.query(PriceHistory).filter(
                PriceHistory.vehicle_id == vehicle_id
            ).order_by(desc(PriceHistory.recorded_at)).first()
            
            # Calculate price change
            price_change = 0.0
            change_percentage = 0.0
            
            if latest_price:
                price_change = new_price - latest_price.price
                if latest_price.price > 0:
                    change_percentage = (price_change / latest_price.price) * 100
                
                # Mark previous price as inactive
                latest_price.is_active = False
            
            # Calculate days on market
            first_price = self.db.query(PriceHistory).filter(
                PriceHistory.vehicle_id == vehicle_id
            ).order_by(asc(PriceHistory.recorded_at)).first()
            
            days_on_market = 0
            if first_price:
                days_on_market = (datetime.utcnow() - first_price.recorded_at).days
            
            # Determine market position
            market_position = self._analyze_market_position(vehicle, new_price)
            
            # Create new price history record
            price_history = PriceHistory(
                vehicle_id=vehicle_id,
                price=new_price,
                currency=vehicle.currency or "EUR",
                price_change=price_change,
                change_percentage=change_percentage,
                original_price=vehicle.original_price,
                price_type=vehicle.price_type or "fixed",
                market_position=market_position,
                days_on_market=days_on_market,
                source_website=source_website,
                source_url=source_url,
                is_active=True
            )
            
            self.db.add(price_history)
            
            # Update vehicle's current price
            vehicle.price = new_price
            vehicle.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(price_history)
            
            # Check for price alerts
            if abs(change_percentage) >= 5:  # 5% change threshold
                self._trigger_price_alerts(vehicle, price_history)
            
            logger.info(f"Recorded price change for vehicle {vehicle_id}: €{new_price} ({change_percentage:+.1f}%)")
            return price_history
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record price change: {str(e)}")
            raise
    
    def get_price_history(self, vehicle_id: int, days: int = 30) -> List[PriceHistory]:
        """Get price history for a vehicle"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return self.db.query(PriceHistory).filter(
            and_(
                PriceHistory.vehicle_id == vehicle_id,
                PriceHistory.recorded_at >= cutoff_date
            )
        ).order_by(asc(PriceHistory.recorded_at)).all()
    
    def analyze_price_trend(self, vehicle_id: int, days: int = 30) -> Dict[str, Any]:
        """Analyze price trend for a vehicle"""
        price_history = self.get_price_history(vehicle_id, days)
        
        if len(price_history) < 2:
            return {
                "trend": "insufficient_data",
                "total_change": 0.0,
                "total_change_percentage": 0.0,
                "average_price": price_history[0].price if price_history else 0.0,
                "price_volatility": 0.0,
                "data_points": len(price_history)
            }
        
        prices = [p.price for p in price_history]
        first_price = prices[0]
        last_price = prices[-1]
        
        total_change = last_price - first_price
        total_change_percentage = (total_change / first_price) * 100 if first_price > 0 else 0.0
        
        # Determine trend
        if total_change_percentage > 2:
            trend = "increasing"
        elif total_change_percentage < -2:
            trend = "decreasing"
        else:
            trend = "stable"
        
        # Calculate volatility (standard deviation of price changes)
        if len(prices) > 2:
            price_changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            volatility = (sum([(x - mean(price_changes))**2 for x in price_changes]) / len(price_changes))**0.5
        else:
            volatility = 0.0
        
        return {
            "trend": trend,
            "total_change": total_change,
            "total_change_percentage": total_change_percentage,
            "average_price": mean(prices),
            "median_price": median(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "price_volatility": volatility,
            "data_points": len(price_history),
            "first_recorded": price_history[0].recorded_at,
            "last_recorded": price_history[-1].recorded_at
        }
    
    def get_price_alerts_summary(self, vehicle_id: int) -> Dict[str, Any]:
        """Get summary of price alerts for a vehicle"""
        price_history = self.get_price_history(vehicle_id, 90)  # Last 90 days
        
        significant_changes = [p for p in price_history if abs(p.change_percentage or 0) >= 5]
        price_drops = [p for p in significant_changes if (p.change_percentage or 0) < 0]
        price_increases = [p for p in significant_changes if (p.change_percentage or 0) > 0]
        
        return {
            "total_significant_changes": len(significant_changes),
            "price_drops": len(price_drops),
            "price_increases": len(price_increases),
            "largest_drop": min([p.change_percentage for p in price_drops], default=0),
            "largest_increase": max([p.change_percentage for p in price_increases], default=0),
            "recent_changes": significant_changes[-5:] if significant_changes else []
        }
    
    def predict_price_trend(self, vehicle_id: int, days_ahead: int = 30) -> Dict[str, Any]:
        """Simple price trend prediction based on historical data"""
        price_history = self.get_price_history(vehicle_id, 60)  # Use 60 days of data
        
        if len(price_history) < 5:
            return {
                "prediction": "insufficient_data",
                "confidence": 0.0,
                "predicted_price": None,
                "prediction_range": None
            }
        
        # Simple linear regression on price changes
        prices = [p.price for p in price_history]
        days = [(p.recorded_at - price_history[0].recorded_at).days for p in price_history]
        
        # Calculate trend slope
        n = len(prices)
        sum_x = sum(days)
        sum_y = sum(prices)
        sum_xy = sum(days[i] * prices[i] for i in range(n))
        sum_x2 = sum(x**2 for x in days)
        
        if n * sum_x2 - sum_x**2 == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
        
        intercept = (sum_y - slope * sum_x) / n
        
        # Predict future price
        future_day = days[-1] + days_ahead
        predicted_price = slope * future_day + intercept
        
        # Calculate confidence based on data consistency
        actual_prices = prices
        predicted_prices = [slope * d + intercept for d in days]
        errors = [abs(actual_prices[i] - predicted_prices[i]) for i in range(len(actual_prices))]
        avg_error = mean(errors)
        confidence = max(0, min(1, 1 - (avg_error / mean(actual_prices))))
        
        # Determine prediction category
        current_price = prices[-1]
        price_change_percentage = ((predicted_price - current_price) / current_price) * 100
        
        if price_change_percentage > 5:
            prediction = "increasing"
        elif price_change_percentage < -5:
            prediction = "decreasing"
        else:
            prediction = "stable"
        
        return {
            "prediction": prediction,
            "confidence": confidence,
            "predicted_price": predicted_price,
            "current_price": current_price,
            "predicted_change": predicted_price - current_price,
            "predicted_change_percentage": price_change_percentage,
            "prediction_range": {
                "min": predicted_price - avg_error,
                "max": predicted_price + avg_error
            },
            "data_points_used": len(price_history),
            "prediction_horizon_days": days_ahead
        }
    
    def get_market_comparison(self, vehicle_id: int) -> Dict[str, Any]:
        """Compare vehicle price with similar vehicles in the market"""
        vehicle = self.db.query(VehicleListing).filter(VehicleListing.id == vehicle_id).first()
        if not vehicle:
            return {}
        
        # Find similar vehicles (same make, model, similar year)
        year_range = 2  # +/- 2 years
        similar_vehicles = self.db.query(VehicleListing).filter(
            and_(
                VehicleListing.make == vehicle.make,
                VehicleListing.model == vehicle.model,
                VehicleListing.year >= (vehicle.year or 0) - year_range,
                VehicleListing.year <= (vehicle.year or 9999) + year_range,
                VehicleListing.id != vehicle_id,
                VehicleListing.is_active == True,
                VehicleListing.price.isnot(None)
            )
        ).all()
        
        if not similar_vehicles:
            return {"comparison": "no_similar_vehicles"}
        
        similar_prices = [v.price for v in similar_vehicles if v.price]
        
        if not similar_prices:
            return {"comparison": "no_price_data"}
        
        avg_market_price = mean(similar_prices)
        median_market_price = median(similar_prices)
        min_market_price = min(similar_prices)
        max_market_price = max(similar_prices)
        
        # Calculate position
        price_percentile = sum(1 for p in similar_prices if p <= vehicle.price) / len(similar_prices)
        
        if price_percentile <= 0.25:
            position = "below_market"
        elif price_percentile >= 0.75:
            position = "above_market"
        else:
            position = "at_market"
        
        return {
            "comparison": "available",
            "market_position": position,
            "vehicle_price": vehicle.price,
            "market_average": avg_market_price,
            "market_median": median_market_price,
            "market_range": {
                "min": min_market_price,
                "max": max_market_price
            },
            "price_difference_from_average": vehicle.price - avg_market_price,
            "price_difference_percentage": ((vehicle.price - avg_market_price) / avg_market_price) * 100,
            "percentile": price_percentile * 100,
            "similar_vehicles_count": len(similar_vehicles)
        }
    
    def _analyze_market_position(self, vehicle: VehicleListing, price: float) -> str:
        """Analyze market position for a vehicle price"""
        market_comparison = self.get_market_comparison(vehicle.id)
        
        if market_comparison.get("comparison") == "available":
            return market_comparison.get("market_position", "unknown")
        
        return "unknown"
    
    def _trigger_price_alerts(self, vehicle: VehicleListing, price_history: PriceHistory):
        """Trigger price alerts for significant price changes"""
        try:
            # This would integrate with the alert system
            # For now, just log the significant change
            change_type = "drop" if price_history.change_percentage < 0 else "increase"
            logger.info(
                f"Significant price {change_type} detected for {vehicle.make} {vehicle.model}: "
                f"{price_history.change_percentage:+.1f}% to €{price_history.price}"
            )
            
            # TODO: Integrate with user alert system to notify users watching this vehicle
            
        except Exception as e:
            logger.error(f"Failed to trigger price alerts: {str(e)}")
    
    def get_price_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get overall price statistics for the system"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all price changes in the period
        price_changes = self.db.query(PriceHistory).filter(
            and_(
                PriceHistory.recorded_at >= cutoff_date,
                PriceHistory.price_change.isnot(None)
            )
        ).all()
        
        if not price_changes:
            return {"period_days": days, "total_changes": 0}
        
        changes = [p.price_change for p in price_changes if p.price_change]
        percentages = [p.change_percentage for p in price_changes if p.change_percentage]
        
        price_drops = [p for p in price_changes if (p.change_percentage or 0) < 0]
        price_increases = [p for p in price_changes if (p.change_percentage or 0) > 0]
        
        return {
            "period_days": days,
            "total_changes": len(price_changes),
            "price_drops": len(price_drops),
            "price_increases": len(price_increases),
            "average_change": mean(changes) if changes else 0,
            "average_change_percentage": mean(percentages) if percentages else 0,
            "largest_drop_percentage": min(percentages) if percentages else 0,
            "largest_increase_percentage": max(percentages) if percentages else 0,
            "vehicles_with_changes": len(set(p.vehicle_id for p in price_changes))
        }
