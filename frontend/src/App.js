import { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "./components/ui/card";
import { Textarea } from "./components/ui/textarea";
import { Input } from "./components/ui/input";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Separator } from "./components/ui/separator";
import { Calendar, BookOpen, MessageSquare, CheckCircle, Clock, Trash2, Plus, Sparkles } from "lucide-react";
import { useToast } from "./hooks/use-toast";
import { Toaster } from "./components/ui/toaster";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [notes, setNotes] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // Note State
  const [noteTitle, setNoteTitle] = useState("");
  const [noteContent, setNoteContent] = useState("");

  // Schedule State
  const [scheduleInput, setScheduleInput] = useState("");

  // Task Extraction State
  const [conversationText, setConversationText] = useState("");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [notesRes, tasksRes, eventsRes] = await Promise.all([
        axios.get(`${API}/notes`),
        axios.get(`${API}/tasks`),
        axios.get(`${API}/schedule`)
      ]);
      setNotes(notesRes.data);
      setTasks(tasksRes.data);
      setEvents(eventsRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast({
        title: "Error",
        description: "Failed to fetch data",
        variant: "destructive"
      });
    }
  };

  const createNote = async () => {
    if (!noteTitle.trim() || !noteContent.trim()) {
      toast({
        title: "Error",
        description: "Please enter both title and content",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/notes`, {
        title: noteTitle,
        content: noteContent
      });
      setNotes([response.data, ...notes]);
      setNoteTitle("");
      setNoteContent("");
      toast({
        title: "Success",
        description: "Note created with AI summary and keywords!"
      });
    } catch (error) {
      console.error("Error creating note:", error);
      toast({
        title: "Error",
        description: "Failed to create note",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const parseSchedule = async () => {
    if (!scheduleInput.trim()) {
      toast({
        title: "Error",
        description: "Please enter a scheduling request",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/schedule/parse`, {
        natural_language: scheduleInput
      });
      setEvents([response.data, ...events]);
      setScheduleInput("");
      toast({
        title: "Success",
        description: "Schedule parsed and created!"
      });
    } catch (error) {
      console.error("Error parsing schedule:", error);
      toast({
        title: "Error",
        description: "Failed to parse schedule",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const extractTasks = async () => {
    if (!conversationText.trim()) {
      toast({
        title: "Error",
        description: "Please enter conversation text",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/tasks/extract`, {
        conversation_text: conversationText
      });
      setTasks([...response.data.tasks, ...tasks]);
      setConversationText("");
      toast({
        title: "Success",
        description: `Extracted ${response.data.tasks.length} tasks from conversation!`
      });
    } catch (error) {
      console.error("Error extracting tasks:", error);
      toast({
        title: "Error",
        description: "Failed to extract tasks",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const completeTask = async (taskId) => {
    try {
      await axios.put(`${API}/tasks/${taskId}/complete`);
      setTasks(tasks.map(task => 
        task.id === taskId ? { ...task, completed: true } : task
      ));
      toast({
        title: "Success",
        description: "Task marked as complete!"
      });
    } catch (error) {
      console.error("Error completing task:", error);
      toast({
        title: "Error",
        description: "Failed to complete task",
        variant: "destructive"
      });
    }
  };

  const deleteTask = async (taskId) => {
    try {
      await axios.delete(`${API}/tasks/${taskId}`);
      setTasks(tasks.filter(task => task.id !== taskId));
      toast({
        title: "Success",
        description: "Task deleted successfully!"
      });
    } catch (error) {
      console.error("Error deleting task:", error);
      toast({
        title: "Error",
        description: "Failed to delete task",
        variant: "destructive"
      });
    }
  };

  const deleteNote = async (noteId) => {
    try {
      await axios.delete(`${API}/notes/${noteId}`);
      setNotes(notes.filter(note => note.id !== noteId));
      toast({
        title: "Success",
        description: "Note deleted successfully!"
      });
    } catch (error) {
      console.error("Error deleting note:", error);
      toast({
        title: "Error",
        description: "Failed to delete note",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-800">Orbi</h1>
                <p className="text-sm text-slate-600">Smart Productivity Assistant</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-600">Welcome back, Student!</p>
              <p className="text-xs text-slate-500">Let's boost your productivity</p>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-purple-700 text-white py-16">
        <div className="container mx-auto px-6 text-center">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-4xl font-bold mb-4">Your AI-Powered Study Companion</h2>
            <p className="text-xl opacity-90 mb-8">
              Transform your notes, schedule your time, and extract tasks from conversations with intelligent AI assistance
            </p>
            <img 
              src="https://images.unsplash.com/photo-1559911352-816690ce34cc" 
              alt="Student using laptop"
              className="w-64 h-48 object-cover rounded-2xl mx-auto shadow-2xl border-4 border-white/20"
            />
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-12">
        <Tabs defaultValue="notes" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8">
            <TabsTrigger value="notes" className="flex items-center space-x-2">
              <BookOpen className="w-4 h-4" />
              <span>Smart Notes</span>
            </TabsTrigger>
            <TabsTrigger value="schedule" className="flex items-center space-x-2">
              <Calendar className="w-4 h-4" />
              <span>AI Scheduler</span>
            </TabsTrigger>
            <TabsTrigger value="tasks" className="flex items-center space-x-2">
              <MessageSquare className="w-4 h-4" />
              <span>Task Extractor</span>
            </TabsTrigger>
          </TabsList>

          {/* Smart Notes Tab */}
          <TabsContent value="notes" className="space-y-6">
            <Card className="border-2 border-blue-100">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BookOpen className="w-5 h-5 text-blue-600" />
                  <span>Create Smart Note</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  placeholder="Note title..."
                  value={noteTitle}
                  onChange={(e) => setNoteTitle(e.target.value)}
                  className="text-lg"
                />
                <Textarea
                  placeholder="Start writing your note... AI will automatically generate summary and keywords!"
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  className="min-h-32"
                />
                <Button 
                  onClick={createNote} 
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                >
                  {loading ? (
                    <>
                      <Clock className="w-4 h-4 mr-2 animate-spin" />
                      Creating with AI...
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4 mr-2" />
                      Create Smart Note
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Notes List */}
            <div className="grid gap-4">
              {notes.map((note) => (
                <Card key={note.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-lg text-slate-800">{note.title}</CardTitle>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteNote(note.id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <p className="text-sm font-medium text-blue-800 mb-1">AI Summary:</p>
                      <p className="text-blue-700">{note.summary}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {note.keywords.map((keyword, index) => (
                        <Badge key={index} variant="secondary" className="bg-purple-100 text-purple-700">
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                    <Separator />
                    <div className="bg-slate-50 p-3 rounded-lg">
                      <p className="text-sm text-slate-600 whitespace-pre-wrap">{note.content}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* AI Scheduler Tab */}
          <TabsContent value="schedule" className="space-y-6">
            <Card className="border-2 border-green-100">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Calendar className="w-5 h-5 text-green-600" />
                  <span>Natural Language Scheduler</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-green-50 p-4 rounded-lg">
                  <p className="text-sm text-green-800 mb-2">Try saying:</p>
                  <ul className="text-sm text-green-700 space-y-1">
                    <li>• "Schedule study session for Math tomorrow at 3 PM"</li>
                    <li>• "Meet with Sarah for project discussion on Friday at 2:30"</li>
                    <li>• "Chemistry exam preparation next Monday morning"</li>
                  </ul>
                </div>
                <Textarea
                  placeholder="Tell me what you want to schedule..."
                  value={scheduleInput}
                  onChange={(e) => setScheduleInput(e.target.value)}
                  className="min-h-24"
                />
                <Button 
                  onClick={parseSchedule} 
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700"
                >
                  {loading ? (
                    <>
                      <Clock className="w-4 h-4 mr-2 animate-spin" />
                      Parsing with AI...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Parse & Schedule
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Schedule List */}
            <div className="grid gap-4">
              {events.map((event) => (
                <Card key={event.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <h3 className="font-semibold text-slate-800">{event.title}</h3>
                        <p className="text-sm text-slate-600">{event.description}</p>
                        <div className="flex items-center space-x-4 text-sm text-slate-500">
                          <span className="flex items-center space-x-1">
                            <Calendar className="w-3 h-3" />
                            <span>{event.date}</span>
                          </span>
                          <span className="flex items-center space-x-1">
                            <Clock className="w-3 h-3" />
                            <span>{event.time}</span>
                          </span>
                        </div>
                      </div>
                      <div className="w-12 h-12 bg-gradient-to-r from-green-400 to-blue-500 rounded-lg flex items-center justify-center">
                        <Calendar className="w-6 h-6 text-white" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Task Extractor Tab */}
          <TabsContent value="tasks" className="space-y-6">
            <Card className="border-2 border-orange-100">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MessageSquare className="w-5 h-5 text-orange-600" />
                  <span>Smart Task Extractor</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-orange-50 p-4 rounded-lg">
                  <p className="text-sm text-orange-800 mb-2">Paste any conversation and I'll extract tasks:</p>
                  <p className="text-sm text-orange-700">
                    "Hey, can you submit the physics assignment by Friday? Also, don't forget about the group meeting on Tuesday."
                  </p>
                </div>
                <Textarea
                  placeholder="Paste your conversation, email, or chat here..."
                  value={conversationText}
                  onChange={(e) => setConversationText(e.target.value)}
                  className="min-h-32"
                />
                <Button 
                  onClick={extractTasks} 
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700"
                >
                  {loading ? (
                    <>
                      <Clock className="w-4 h-4 mr-2 animate-spin" />
                      Extracting tasks...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Extract Tasks
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Tasks List */}
            <div className="grid gap-4">
              {tasks.map((task) => (
                <Card key={task.id} className={`hover:shadow-md transition-shadow ${task.completed ? 'opacity-60' : ''}`}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="space-y-2 flex-1">
                        <div className="flex items-center space-x-2">
                          <h3 className={`font-semibold ${task.completed ? 'line-through text-slate-500' : 'text-slate-800'}`}>
                            {task.title}
                          </h3>
                          <Badge 
                            variant={task.priority === 'high' ? 'destructive' : task.priority === 'medium' ? 'default' : 'secondary'}
                            className="text-xs"
                          >
                            {task.priority}
                          </Badge>
                        </div>
                        {task.description && (
                          <p className="text-sm text-slate-600">{task.description}</p>
                        )}
                        {task.deadline && (
                          <p className="text-sm text-red-600 font-medium">Due: {task.deadline}</p>
                        )}
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        {!task.completed && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => completeTask(task.id)}
                            className="text-green-600 hover:text-green-700"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteTask(task.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-8 mt-16">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="font-semibold text-slate-800">Orbi</p>
                <p className="text-xs text-slate-600">Powered by AI</p>
              </div>
            </div>
            <p className="text-sm text-slate-600">© 2025 Orbi. Your smart productivity companion.</p>
          </div>
        </div>
      </footer>

      <Toaster />
    </div>
  );
}

export default App;