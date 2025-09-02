import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Input } from '../ui/Input';
import { ScreeningTemplate, ScreeningCategory } from '../../types/screening';
import { screeningService } from '../../services/screeningService';
import { Search, Star, TrendingUp, Shield, Zap, Target } from 'lucide-react';

interface ScreeningTemplatesProps {
  onSelectTemplate: (template: ScreeningTemplate) => void;
}

const ScreeningTemplates: React.FC<ScreeningTemplatesProps> = ({ onSelectTemplate }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<ScreeningCategory | 'all'>('all');

  const { data: templates, isLoading } = useQuery({
    queryKey: ['screening-templates', selectedCategory],
    queryFn: () => screeningService.getScreeningTemplates(selectedCategory === 'all' ? undefined : selectedCategory),
  });

  const { data: popularTemplates } = useQuery({
    queryKey: ['popular-screenings'],
    queryFn: () => screeningService.getPopularScreenings(6),
  });

  const filteredTemplates = templates?.filter(template =>
    template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.description.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const categories: Array<{ id: ScreeningCategory | 'all'; name: string; icon: React.ComponentType<any> }> = [
    { id: 'all', name: 'All Templates', icon: Target },
    { id: 'value', name: 'Value', icon: TrendingUp },
    { id: 'growth', name: 'Growth', icon: Zap },
    { id: 'income', name: 'Income', icon: Star },
    { id: 'technical', name: 'Technical', icon: Shield },
  ];

  const getCategoryIcon = (category: ScreeningCategory) => {
    switch (category) {
      case 'value': return TrendingUp;
      case 'growth': return Zap;
      case 'income': return Star;
      case 'technical': return Shield;
      default: return Target;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="h-32 bg-slate-200 rounded-lg"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            icon={Search}
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {categories.map((category) => {
            const Icon = category.icon;
            return (
              <Button
                key={category.id}
                variant={selectedCategory === category.id ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setSelectedCategory(category.id)}
                className="flex items-center gap-2"
              >
                <Icon className="w-4 h-4" />
                {category.name}
              </Button>
            );
          })}
        </div>
      </div>

      {/* Popular Templates */}
      {popularTemplates && popularTemplates.length > 0 && selectedCategory === 'all' && !searchQuery && (
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Star className="w-5 h-5 text-yellow-500" />
            Popular Templates
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {popularTemplates.slice(0, 6).map((template) => {
              const CategoryIcon = getCategoryIcon(template.category);
              return (
                <Card key={template.id} className="p-4 hover:shadow-md transition-shadow cursor-pointer" onClick={() => onSelectTemplate(template)}>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <CategoryIcon className="w-4 h-4 text-slate-600" />
                      <Badge variant="outline" className="text-xs">
                        {template.category}
                      </Badge>
                    </div>
                    <Star className="w-4 h-4 text-yellow-500 fill-current" />
                  </div>
                  <h4 className="font-medium text-slate-900 mb-2">{template.name}</h4>
                  <p className="text-sm text-slate-600 mb-3">{template.description}</p>
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>{template.filters.length} filters</span>
                    <span>{template.usage_count?.toLocaleString()} uses</span>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* All Templates */}
      <div>
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          {selectedCategory === 'all' ? 'All Templates' : categories.find(c => c.id === selectedCategory)?.name + ' Templates'}
          <span className="ml-2 text-sm font-normal text-slate-500">
            ({filteredTemplates.length} templates)
          </span>
        </h3>
        
        {filteredTemplates.length === 0 ? (
          <Card className="p-8 text-center">
            <div className="text-slate-400 mb-2">
              <Search className="w-12 h-12 mx-auto" />
            </div>
            <h4 className="text-lg font-medium text-slate-900 mb-2">No templates found</h4>
            <p className="text-slate-600">
              {searchQuery ? 'Try adjusting your search terms or filters.' : 'No templates available for this category.'}
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTemplates.map((template) => {
              const CategoryIcon = getCategoryIcon(template.category);
              return (
                <Card key={template.id} className="p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <CategoryIcon className="w-4 h-4 text-slate-600" />
                      <Badge variant="outline" className="text-xs">
                        {template.category}
                      </Badge>
                    </div>
                    {template.is_featured && (
                      <Star className="w-4 h-4 text-yellow-500 fill-current" />
                    )}
                  </div>
                  <h4 className="font-medium text-slate-900 mb-2">{template.name}</h4>
                  <p className="text-sm text-slate-600 mb-4">{template.description}</p>
                  <div className="flex items-center justify-between mb-4 text-xs text-slate-500">
                    <span>{template.filters.length} filters</span>
                    <span>{template.usage_count?.toLocaleString()} uses</span>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => onSelectTemplate(template)}
                    className="w-full"
                  >
                    Use Template
                  </Button>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ScreeningTemplates;