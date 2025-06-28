import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import { Car, Check, Trash2, ExternalLink, AlertCircle, Info, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';

interface NotificationItemProps {
  notification: {
    id: number;
    title: string;
    message: string;
    notification_type: string;
    priority: number;
    is_read: boolean;
    created_at: string;
    content_data?: {
      listing?: {
        id: number;
        make: string;
        model: string;
        year?: number;
        price?: number;
        city?: string;
        listing_url?: string;
        primary_image_url?: string;
      };
      alert?: {
        id: number;
        name: string;
      };
      match?: {
        score: number;
        is_perfect_match: boolean;
      };
    };
  };
  onAction: (id: number, action: 'read' | 'delete') => void;
}

export const NotificationItem: React.FC<NotificationItemProps> = ({ notification, onAction }) => {
  const { content_data } = notification;
  const listing = content_data?.listing;
  const alert = content_data?.alert;
  const match = content_data?.match;

  const getPriorityIcon = (priority: number) => {
    switch (priority) {
      case 5:
      case 4:
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 3:
        return <AlertCircle className="h-4 w-4 text-orange-500" />;
      case 2:
        return <Info className="h-4 w-4 text-blue-500" />;
      default:
        return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
  };

  const getPriorityColor = (priority: number) => {
    switch (priority) {
      case 5:
      case 4:
        return 'border-l-red-500';
      case 3:
        return 'border-l-orange-500';
      case 2:
        return 'border-l-blue-500';
      default:
        return 'border-l-green-500';
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-EU', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0
    }).format(price);
  };

  const handleViewListing = () => {
    if (listing?.listing_url) {
      window.open(listing.listing_url, '_blank');
    }
  };

  return (
    <div
      className={`p-4 border-l-4 ${getPriorityColor(notification.priority)} ${
        !notification.is_read ? 'bg-blue-50' : 'bg-white'
      } hover:bg-gray-50 transition-colors`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center space-x-2 mb-2">
            {getPriorityIcon(notification.priority)}
            <h3 className={`text-sm font-medium ${!notification.is_read ? 'text-gray-900' : 'text-gray-700'}`}>
              {notification.title}
            </h3>
            {!notification.is_read && (
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
            )}
          </div>

          {/* Vehicle Information */}
          {listing && (
            <Card className="mb-3 p-3 bg-gray-50">
              <div className="flex items-start space-x-3">
                {listing.primary_image_url ? (
                  <img
                    src={listing.primary_image_url}
                    alt={`${listing.make} ${listing.model}`}
                    className="w-16 h-12 object-cover rounded"
                  />
                ) : (
                  <div className="w-16 h-12 bg-gray-200 rounded flex items-center justify-center">
                    <Car className="h-6 w-6 text-gray-400" />
                  </div>
                )}
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-medium text-gray-900">
                      {listing.make} {listing.model}
                    </h4>
                    {listing.year && (
                      <Badge variant="secondary" className="text-xs">
                        {listing.year}
                      </Badge>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                    {listing.price && (
                      <span className="font-semibold text-green-600">
                        {formatPrice(listing.price)}
                      </span>
                    )}
                    {listing.city && (
                      <span>{listing.city}</span>
                    )}
                  </div>

                  {match && (
                    <div className="mt-2">
                      <Badge
                        variant={match.is_perfect_match ? "default" : "secondary"}
                        className="text-xs"
                      >
                        {match.is_perfect_match ? "Perfect Match" : `${Math.round(match.score * 100)}% Match`}
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          )}

          {/* Message */}
          <p className="text-sm text-gray-600 mb-2">{notification.message}</p>

          {/* Alert Information */}
          {alert && (
            <div className="text-xs text-gray-500 mb-2">
              Alert: <span className="font-medium">{alert.name}</span>
            </div>
          )}

          {/* Timestamp */}
          <div className="text-xs text-gray-400">
            {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col space-y-1 ml-4">
          {!notification.is_read && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onAction(notification.id, 'read')}
              className="h-8 w-8 p-0"
            >
              <Check className="h-4 w-4" />
            </Button>
          )}
          
          {listing?.listing_url && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleViewListing}
              className="h-8 w-8 p-0"
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
          )}
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onAction(notification.id, 'delete')}
            className="h-8 w-8 p-0 text-red-500 hover:text-red-700"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default NotificationItem;
