import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Input } from '../ui/Input';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { BookmarkFolder, CreateBookmarkFolderRequest } from '../../types/education';
import { educationService } from '../../services/educationService';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { 
  Bookmark,
  Star,
  Folder,
  Plus,
  Search,
  MoreVertical,
  Edit3,
  Trash2,
  Clock,
  Eye,
  BookOpen,
  Video,
  Award,
  Play,
  X
} from 'lucide-react';

interface BookmarksProps {
  onContentSelect?: (contentId: string) => void;
}

const Bookmarks: React.FC<BookmarksProps> = ({ onContentSelect }) => {
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [newFolderDescription, setNewFolderDescription] = useState('');

  const queryClient = useQueryClient();

  // Fetch bookmarks
  const { data: bookmarksData, isLoading: bookmarksLoading } = useQuery({
    queryKey: ['bookmarks', selectedFolderId],
    queryFn: () => educationService.getBookmarks(selectedFolderId || undefined),
  });

  // Create folder mutation
  const createFolderMutation = useMutation({
    mutationFn: (request: CreateBookmarkFolderRequest) => educationService.createBookmarkFolder(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookmarks'] });
      setIsCreatingFolder(false);
      setNewFolderName('');
      setNewFolderDescription('');
    },
  });

  // Delete bookmark mutation
  const deleteBookmarkMutation = useMutation({
    mutationFn: (bookmarkId: string) => educationService.deleteBookmark(bookmarkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookmarks'] });
    },
  });

  // Delete folder mutation
  const deleteFolderMutation = useMutation({
    mutationFn: (folderId: string) => educationService.deleteBookmarkFolder(folderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookmarks'] });
      if (selectedFolderId === selectedFolderId) {
        setSelectedFolderId(null);
      }
    },
  });

  const filteredBookmarks = bookmarksData?.bookmarks.filter(bookmark =>
    bookmark.content.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    bookmark.content.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (bookmark.notes && bookmark.notes.toLowerCase().includes(searchQuery.toLowerCase()))
  ) || [];

  const getContentIcon = (type: string) => {
    switch (type) {
      case 'video': return Video;
      case 'course': return Award;
      case 'tutorial': return Play;
      default: return BookOpen;
    }
  };

  const handleCreateFolder = () => {
    if (newFolderName.trim()) {
      createFolderMutation.mutate({
        name: newFolderName.trim(),
        description: newFolderDescription.trim() || undefined,
      });
    }
  };

  if (bookmarksLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse h-12 bg-slate-200 rounded-lg"></div>
        <div className="animate-pulse h-64 bg-slate-200 rounded-lg"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Bookmark className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">My Bookmarks</h2>
            <p className="text-slate-600">Saved content for later reference</p>
          </div>
        </div>
        <Button
          onClick={() => setIsCreatingFolder(true)}
          className="flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Folder
        </Button>
      </div>

      {/* Create Folder Modal */}
      {isCreatingFolder && (
        <Card className="p-4 border-primary-200 bg-primary-50">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-slate-900">Create New Folder</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setIsCreatingFolder(false);
                  setNewFolderName('');
                  setNewFolderDescription('');
                }}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            <div>
              <Input
                placeholder="Folder name"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                className="mb-3"
              />
              <Input
                placeholder="Description (optional)"
                value={newFolderDescription}
                onChange={(e) => setNewFolderDescription(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleCreateFolder}
                loading={createFolderMutation.isPending}
                disabled={!newFolderName.trim()}
              >
                Create Folder
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setIsCreatingFolder(false);
                  setNewFolderName('');
                  setNewFolderDescription('');
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Folders Sidebar */}
        <div className="lg:col-span-1">
          <Card className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-slate-900">Folders</h3>
              <Badge variant="secondary">
                {bookmarksData?.folders?.length || 0}
              </Badge>
            </div>
            
            <div className="space-y-2">
              {/* All Bookmarks */}
              <button
                onClick={() => setSelectedFolderId(null)}
                className={`w-full flex items-center justify-between p-3 rounded-lg text-left transition-colors ${
                  selectedFolderId === null
                    ? 'bg-primary-50 text-primary-700 border border-primary-200'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Bookmark className="w-4 h-4" />
                  <span className="font-medium">All Bookmarks</span>
                </div>
                <Badge variant="outline" className="text-xs">
                  {bookmarksData?.total_count || 0}
                </Badge>
              </button>

              {/* Individual Folders */}
              {bookmarksData?.folders?.map((folder) => (
                <div key={folder.id} className="relative">
                  <button
                    onClick={() => setSelectedFolderId(folder.id)}
                    className={`w-full flex items-center justify-between p-3 rounded-lg text-left transition-colors ${
                      selectedFolderId === folder.id
                        ? 'bg-primary-50 text-primary-700 border border-primary-200'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Folder className="w-4 h-4" />
                      <span className="font-medium truncate">{folder.name}</span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {folder.bookmark_count}
                    </Badge>
                  </button>
                  {selectedFolderId === folder.id && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteFolderMutation.mutate(folder.id)}
                      loading={deleteFolderMutation.isPending}
                      className="absolute top-2 right-8 p-1 text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Bookmarks Content */}
        <div className="lg:col-span-3 space-y-4">
          {/* Search */}
          <div>
            <Input
              placeholder="Search bookmarks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              icon={Search}
            />
          </div>

          {/* Current Folder Info */}
          {selectedFolderId && bookmarksData?.folders && (
            <Card className="p-4 bg-slate-50">
              {(() => {
                const folder = bookmarksData.folders.find(f => f.id === selectedFolderId);
                return folder ? (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium text-slate-900 flex items-center gap-2">
                        <Folder className="w-4 h-4" />
                        {folder.name}
                      </h3>
                      <Badge variant="outline">{folder.bookmark_count} bookmarks</Badge>
                    </div>
                    {folder.description && (
                      <p className="text-sm text-slate-600">{folder.description}</p>
                    )}
                  </div>
                ) : null;
              })()}
            </Card>
          )}

          {/* Bookmarks Grid */}
          {filteredBookmarks.length === 0 ? (
            <Card className="p-12 text-center">
              <div className="text-slate-400 mb-4">
                <Bookmark className="w-12 h-12 mx-auto" />
              </div>
              <h3 className="text-lg font-medium text-slate-900 mb-2">
                {searchQuery ? 'No bookmarks found' : 'No bookmarks yet'}
              </h3>
              <p className="text-slate-600 mb-4">
                {searchQuery 
                  ? 'Try adjusting your search terms.' 
                  : 'Start bookmarking content to access it quickly later.'
                }
              </p>
              {searchQuery && (
                <Button variant="outline" onClick={() => setSearchQuery('')}>
                  Clear Search
                </Button>
              )}
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredBookmarks.map((bookmark) => {
                const ContentIcon = getContentIcon(bookmark.content.type);
                return (
                  <Card key={bookmark.id} className="p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start space-x-3">
                      {bookmark.content.thumbnail_url ? (
                        <img
                          src={bookmark.content.thumbnail_url}
                          alt={bookmark.content.title}
                          className="w-16 h-16 object-cover rounded-lg flex-shrink-0"
                        />
                      ) : (
                        <div className="w-16 h-16 bg-gradient-to-br from-primary-100 to-primary-200 rounded-lg flex items-center justify-center flex-shrink-0">
                          <ContentIcon className="w-6 h-6 text-primary-600" />
                        </div>
                      )}
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between mb-2">
                          <h3 
                            className="font-medium text-slate-900 line-clamp-2 cursor-pointer hover:text-primary-600"
                            onClick={() => onContentSelect?.(bookmark.content_id)}
                          >
                            {bookmark.content.title}
                          </h3>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteBookmarkMutation.mutate(bookmark.id)}
                            loading={deleteBookmarkMutation.isPending}
                            className="p-1 text-red-600 hover:text-red-700 flex-shrink-0"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                        
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline" className="text-xs">
                            {bookmark.content.type}
                          </Badge>
                          <Badge variant="secondary" className="text-xs">
                            {bookmark.content.difficulty}
                          </Badge>
                        </div>
                        
                        <p className="text-sm text-slate-600 line-clamp-2 mb-2">
                          {bookmark.content.description}
                        </p>
                        
                        {bookmark.notes && (
                          <div className="p-2 bg-yellow-50 rounded text-sm text-slate-700 mb-2">
                            <span className="font-medium">Note:</span> {bookmark.notes}
                          </div>
                        )}
                        
                        <div className="flex items-center justify-between text-xs text-slate-500">
                          <div className="flex items-center gap-3">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {bookmark.content.duration_minutes || bookmark.content.read_time_minutes}m
                            </span>
                            <span className="flex items-center gap-1">
                              <Star className="w-3 h-3 fill-current text-yellow-500" />
                              {bookmark.content.rating_average.toFixed(1)}
                            </span>
                          </div>
                          <span>
                            Saved {new Date(bookmark.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        
                        <div className="flex items-center justify-between mt-3">
                          <span className="text-sm text-slate-600">
                            by {bookmark.content.author.name}
                          </span>
                          <Button
                            size="sm"
                            onClick={() => onContentSelect?.(bookmark.content_id)}
                            className="flex items-center gap-1"
                          >
                            <Eye className="w-3 h-3" />
                            View
                          </Button>
                        </div>
                        
                        {bookmark.content.progress_percent !== undefined && (
                          <div className="mt-2">
                            <div className="flex justify-between text-xs text-slate-600 mb-1">
                              <span>Progress</span>
                              <span>{bookmark.content.progress_percent}%</span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-1">
                              <div 
                                className="bg-primary-600 h-1 rounded-full"
                                style={{ width: `${bookmark.content.progress_percent}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      {bookmarksData && bookmarksData.bookmarks.length > 0 && (
        <Card className="p-6 bg-gradient-to-r from-blue-50 to-primary-50">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
            <div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Bookmark className="w-6 h-6 text-blue-600" />
              </div>
              <div className="text-2xl font-bold text-slate-900">
                {bookmarksData.total_count}
              </div>
              <div className="text-sm text-slate-600">Total Bookmarks</div>
            </div>
            
            <div>
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Folder className="w-6 h-6 text-yellow-600" />
              </div>
              <div className="text-2xl font-bold text-slate-900">
                {bookmarksData.folders.length}
              </div>
              <div className="text-sm text-slate-600">Folders</div>
            </div>
            
            <div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Star className="w-6 h-6 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-slate-900">
                {bookmarksData.bookmarks.filter(b => b.content.rating_average >= 4.5).length}
              </div>
              <div className="text-sm text-slate-600">Highly Rated</div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default Bookmarks;