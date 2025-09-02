import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Card } from '../ui/Card';
import { XIcon } from 'lucide-react';

const portfolioSchema = z.object({
  name: z.string()
    .min(1, 'Portfolio name is required')
    .max(100, 'Portfolio name must be less than 100 characters'),
  description: z.string()
    .max(500, 'Description must be less than 500 characters')
    .optional(),
  initialCapital: z.number()
    .min(1000, 'Initial capital must be at least $1,000')
    .max(10000000, 'Initial capital cannot exceed $10,000,000'),
  isDefault: z.boolean().optional().default(false),
});

type PortfolioFormData = z.infer<typeof portfolioSchema>;

interface PortfolioCreateModalProps {
  onClose: () => void;
  onSubmit: (data: PortfolioFormData) => void;
  isLoading?: boolean;
}

const PortfolioCreateModal: React.FC<PortfolioCreateModalProps> = ({
  onClose,
  onSubmit,
  isLoading = false,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<PortfolioFormData>({
    resolver: zodResolver(portfolioSchema),
    defaultValues: {
      name: '',
      description: '',
      initialCapital: 50000,
      isDefault: false,
    },
  });

  const handleFormSubmit = (data: PortfolioFormData) => {
    onSubmit(data);
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      onClick={handleBackdropClick}
    >
      <Card className="w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-slate-900">
            Create New Portfolio
          </h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="p-1"
          >
            <XIcon className="w-5 h-5" />
          </Button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          {/* Portfolio Name */}
          <div>
            <Input
              label="Portfolio Name"
              placeholder="e.g., My Options Portfolio"
              {...register('name')}
              error={errors.name?.message}
              required
            />
            <p className="text-xs text-slate-500 mt-1">
              Choose a descriptive name for your portfolio
            </p>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Description <span className="text-slate-500">(optional)</span>
            </label>
            <textarea
              {...register('description')}
              placeholder="e.g., Long-term options strategies focused on earnings plays"
              className="block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm placeholder-slate-400 
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              rows={3}
            />
            {errors.description && (
              <p className="text-sm text-red-600 mt-1">{errors.description.message}</p>
            )}
            <p className="text-xs text-slate-500 mt-1">
              Describe your portfolio strategy and goals
            </p>
          </div>

          {/* Initial Capital */}
          <div>
            <Input
              label="Initial Capital"
              type="number"
              step="1000"
              min="1000"
              max="10000000"
              placeholder="50000"
              {...register('initialCapital', { valueAsNumber: true })}
              error={errors.initialCapital?.message}
              required
            />
            <p className="text-xs text-slate-500 mt-1">
              Starting capital for your portfolio (minimum $1,000)
            </p>
          </div>

          {/* Default Portfolio Option */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="isDefault"
              {...register('isDefault')}
              className="w-4 h-4 text-blue-600 bg-white border-slate-300 rounded focus:ring-blue-500 focus:ring-2"
            />
            <label htmlFor="isDefault" className="text-sm text-slate-700">
              Set as default portfolio
            </label>
          </div>
          <p className="text-xs text-slate-500 -mt-2">
            Your default portfolio will be selected automatically for new trades
          </p>

          {/* Capital Allocation Preview */}
          <div className="bg-slate-50 p-3 rounded-md">
            <h4 className="text-sm font-medium text-slate-900 mb-2">Capital Allocation Preview</h4>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-600">Initial Capital:</span>
                <span className="font-medium">
                  ${(watch('initialCapital') || 0).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Available for Trading:</span>
                <span className="font-medium text-green-600">
                  ${(watch('initialCapital') || 0).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Recommended Max Risk:</span>
                <span className="font-medium text-slate-600">
                  ${Math.floor((watch('initialCapital') || 0) * 0.02).toLocaleString()} (2%)
                </span>
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex space-x-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              className="flex-1"
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="flex-1"
              loading={isLoading}
              disabled={isLoading}
            >
              Create Portfolio
            </Button>
          </div>
        </form>

        {/* Educational Note */}
        <div className="mt-4 p-3 bg-blue-50 rounded-md">
          <h4 className="text-xs font-medium text-blue-900 mb-1">💡 Portfolio Tips</h4>
          <ul className="text-xs text-blue-800 space-y-1">
            <li>• Start with paper trading to test your strategies</li>
            <li>• Never risk more than 2% of your capital per trade</li>
            <li>• Diversify across different symbols and strategies</li>
            <li>• Track your performance regularly</li>
          </ul>
        </div>
      </Card>
    </div>
  );
};

export default PortfolioCreateModal;