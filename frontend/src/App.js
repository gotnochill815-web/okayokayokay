import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// UI Components
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Textarea } from './components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { useToast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';

// Icons
import { 
  PlusIcon, 
  SearchIcon, 
  BookmarkIcon, 
  TagIcon, 
  BrainIcon, 
  LayoutDashboardIcon, 
  LogOutIcon, 
  EditIcon, 
  TrashIcon,
  SparklesIcon,
  HeartIcon,
  FileTextIcon,
  TrendingUpIcon,
  UserIcon
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    setLoading(false);
  }, [token]);

  const login = (userData, authToken) => {
    setUser(userData);
    setToken(authToken);
    localStorage.setItem('token', authToken);
    axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Auth Components
const LoginForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const data = isLogin ? { email, password } : { email, password, name };
      
      const response = await axios.post(`${API}${endpoint}`, data);
      
      login(response.data.user, response.data.token);
      toast({
        title: "Success!",
        description: response.data.message,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Something went wrong",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50 via-blue-50 to-cyan-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-violet-600 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg">
            <BrainIcon className="w-8 h-8 text-white" />
          </div>
          <div>
            <CardTitle className="text-2xl font-bold bg-gradient-to-r from-violet-600 to-blue-600 bg-clip-text text-transparent">
              Smart Notes
            </CardTitle>
            <CardDescription className="text-gray-600 mt-2">
              Your AI-powered productivity assistant
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <Input
                placeholder="Full Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="border-gray-300 focus:border-violet-500"
              />
            )}
            <Input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="border-gray-300 focus:border-violet-500"
            />
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="border-gray-300 focus:border-violet-500"
            />
            <Button 
              type="submit" 
              className="w-full bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-700 hover:to-blue-700 transition-all duration-300"
              disabled={loading}
            >
              {loading ? 'Processing...' : isLogin ? 'Sign In' : 'Create Account'}
            </Button>
          </form>
          
          <div className="mt-6 text-center">
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-violet-600 hover:text-violet-800 font-medium transition-colors"
            >
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Notes Components
const NoteCard = ({ note, onEdit, onDelete, onToggleFavorite }) => {
  const { toast } = useToast();

  const handleAIAction = async (action) => {
    try {
      const response = await axios.post(`${API}/ai/process`, {
        action,
        note_id: note.id
      });
      
      if (action === 'suggest_tags') {
        const tags = JSON.parse(response.data.result);
        toast({
          title: "AI Tag Suggestions",
          description: `Suggested tags: ${tags.join(', ')}`,
        });
      } else {
        toast({
          title: `AI ${action}`,
          description: response.data.result.substring(0, 100) + '...',
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to process AI request",
        variant: "destructive",
      });
    }
  };

  return (
    <Card className="hover:shadow-lg transition-all duration-300 border-0 bg-white/70 backdrop-blur-sm">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <CardTitle className="text-lg font-semibold text-gray-800 line-clamp-1">
            {note.title}
          </CardTitle>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onToggleFavorite(note)}
              className="p-1 h-8 w-8"
            >
              <HeartIcon 
                className={`w-4 h-4 ${note.is_favorite ? 'fill-red-500 text-red-500' : 'text-gray-400'}`} 
              />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(note)}
              className="p-1 h-8 w-8 text-gray-400 hover:text-blue-600"
            >
              <EditIcon className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(note.id)}
              className="p-1 h-8 w-8 text-gray-400 hover:text-red-600"
            >
              <TrashIcon className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-gray-600 text-sm mb-4 line-clamp-3">
          {note.content}
        </p>
        
        {note.summary && (
          <div className="bg-violet-50 p-3 rounded-lg mb-4">
            <p className="text-xs text-violet-700 font-medium mb-1">AI Summary</p>
            <p className="text-sm text-violet-600">{note.summary}</p>
          </div>
        )}
        
        {note.tags && note.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-4">
            {note.tags.map((tag, index) => (
              <Badge key={index} variant="secondary" className="text-xs bg-blue-100 text-blue-700">
                {tag}
              </Badge>
            ))}
          </div>
        )}
        
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>{new Date(note.updated_at).toLocaleDateString()}</span>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleAIAction('insights')}
              className="text-xs p-1 h-6 text-purple-600 hover:text-purple-800"
            >
              <SparklesIcon className="w-3 h-3 mr-1" />
              Insights
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const NoteEditor = ({ note, onSave, onCancel }) => {
  const [title, setTitle] = useState(note?.title || '');
  const [content, setContent] = useState(note?.content || '');
  const [tags, setTags] = useState(note?.tags?.join(', ') || '');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSave = async () => {
    if (!title.trim() || !content.trim()) {
      toast({
        title: "Error",
        description: "Title and content are required",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const noteData = {
        title: title.trim(),
        content: content.trim(),
        tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag)
      };

      if (note) {
        await axios.put(`${API}/notes/${note.id}`, noteData);
        toast({
          title: "Success!",
          description: "Note updated successfully",
        });
      } else {
        await axios.post(`${API}/notes`, noteData);
        toast({
          title: "Success!",
          description: "Note created successfully",
        });
      }
      
      onSave();
    } catch (error) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to save note",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Input
        placeholder="Note title..."
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="text-lg font-semibold border-gray-300 focus:border-violet-500"
      />
      <Textarea
        placeholder="Start writing your note..."
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="min-h-[200px] border-gray-300 focus:border-violet-500 resize-none"
      />
      <Input
        placeholder="Tags (comma separated)..."
        value={tags}
        onChange={(e) => setTags(e.target.value)}
        className="border-gray-300 focus:border-violet-500"
      />
      <div className="flex items-center space-x-3">
        <Button 
          onClick={handleSave} 
          disabled={loading}
          className="bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-700 hover:to-blue-700"
        >
          {loading ? 'Saving...' : note ? 'Update Note' : 'Create Note'}
        </Button>
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  );
};

// Main Dashboard
const Dashboard = () => {
  const [notes, setNotes] = useState([]);
  const [filteredNotes, setFilteredNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState('');
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [editingNote, setEditingNote] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const [userTags, setUserTags] = useState([]);
  const [stats, setStats] = useState({});
  const { user, logout } = useAuth();
  const { toast } = useToast();

  const fetchNotes = async () => {
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      if (selectedTags) params.append('tags', selectedTags);
      if (showFavoritesOnly) params.append('favorites_only', 'true');
      
      const response = await axios.get(`${API}/notes?${params.toString()}`);
      setNotes(response.data);
      setFilteredNotes(response.data);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch notes",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchUserTags = async () => {
    try {
      const response = await axios.get(`${API}/tags`);
      setUserTags(response.data);
    } catch (error) {
      console.error('Failed to fetch tags:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  useEffect(() => {
    fetchNotes();
    fetchUserTags();
    fetchStats();
  }, [searchQuery, selectedTags, showFavoritesOnly]);

  const handleDeleteNote = async (noteId) => {
    try {
      await axios.delete(`${API}/notes/${noteId}`);
      toast({
        title: "Success!",
        description: "Note deleted successfully",
      });
      fetchNotes();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete note",
        variant: "destructive",
      });
    }
  };

  const handleToggleFavorite = async (note) => {
    try {
      await axios.put(`${API}/notes/${note.id}`, {
        is_favorite: !note.is_favorite
      });
      fetchNotes();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update favorite status",
        variant: "destructive",
      });
    }
  };

  const handleNoteSaved = () => {
    setEditingNote(null);
    setIsCreating(false);
    fetchNotes();
    fetchStats();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-violet-50 via-blue-50 to-cyan-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-violet-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your notes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50 via-blue-50 to-cyan-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-violet-600 to-blue-600 rounded-xl flex items-center justify-center">
                <BrainIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-violet-600 to-blue-600 bg-clip-text text-transparent">
                  Smart Notes
                </h1>
                <p className="text-sm text-gray-500">Welcome back, {user?.name}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button
                onClick={() => setIsCreating(true)}
                className="bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-700 hover:to-blue-700"
              >
                <PlusIcon className="w-4 h-4 mr-2" />
                New Note
              </Button>
              <Button variant="ghost" onClick={logout}>
                <LogOutIcon className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <FileTextIcon className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Notes</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_notes || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                  <HeartIcon className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Favorites</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.favorite_notes || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <TrendingUpIcon className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">This Week</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.recent_notes || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <TagIcon className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Tags</p>
                  <p className="text-2xl font-bold text-gray-900">{userTags.length || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Filters */}
        <Card className="mb-8 bg-white/70 backdrop-blur-sm border-0">
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Search notes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 border-gray-300 focus:border-violet-500"
                />
              </div>
              <Input
                placeholder="Filter by tags..."
                value={selectedTags}
                onChange={(e) => setSelectedTags(e.target.value)}
                className="sm:w-48 border-gray-300 focus:border-violet-500"
              />
              <Button
                variant={showFavoritesOnly ? "default" : "outline"}
                onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
                className={showFavoritesOnly ? "bg-red-600 hover:bg-red-700" : ""}
              >
                <HeartIcon className="w-4 h-4 mr-2" />
                Favorites
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Note Editor */}
        {(isCreating || editingNote) && (
          <Card className="mb-8 bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle>{editingNote ? 'Edit Note' : 'Create New Note'}</CardTitle>
            </CardHeader>
            <CardContent>
              <NoteEditor
                note={editingNote}
                onSave={handleNoteSaved}
                onCancel={() => {
                  setEditingNote(null);
                  setIsCreating(false);
                }}
              />
            </CardContent>
          </Card>
        )}

        {/* Notes Grid */}
        {filteredNotes.length === 0 ? (
          <Card className="bg-white/70 backdrop-blur-sm border-0">
            <CardContent className="p-12 text-center">
              <FileTextIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No notes found</h3>
              <p className="text-gray-500">
                {searchQuery || selectedTags ? 'Try adjusting your search or filters' : 'Create your first note to get started!'}
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredNotes.map((note) => (
              <NoteCard
                key={note.id}
                note={note}
                onEdit={setEditingNote}
                onDelete={handleDeleteNote}
                onToggleFavorite={handleToggleFavorite}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-violet-50 via-blue-50 to-cyan-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-violet-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route 
            path="/" 
            element={user ? <Dashboard /> : <LoginForm />} 
          />
          <Route 
            path="*" 
            element={<Navigate to="/" replace />} 
          />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

// App wrapper with AuthProvider
export default function AppWrapper() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}