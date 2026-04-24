import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const IssueManagement = ({ user }) => {
  const [issues, setIssues] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: '', priority: '', type: '' });
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [newIssue, setNewIssue] = useState({
    title: '',
    description: '',
    issue_type: 'RISK_FINDING',
    severity: 'MEDIUM',
    priority: 'P3',
    owner: '',
    app_name: ''
  });

  useEffect(() => {
    fetchIssues();
    fetchStatistics();
  }, [filters]);

  const fetchIssues = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.priority) params.append('priority', filters.priority);
      if (filters.type) params.append('issue_type', filters.type);
      
      const response = await fetch(`${API_URL}/api/issue-management/?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setIssues(data.issues || []);
    } catch (err) {
      console.error('Error fetching issues:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/issue-management/statistics`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setStatistics(data);
    } catch (err) {
      console.error('Error fetching statistics:', err);
    }
  };

  const fetchIssueDetails = async (issueId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/issue-management/${issueId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setSelectedIssue(data);
    } catch (err) {
      console.error('Error fetching issue details:', err);
    }
  };

  const createIssue = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_URL}/api/issue-management/?creator_id=${user?.id || 'user'}&creator_name=${encodeURIComponent(user?.full_name || 'User')}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(newIssue)
        }
      );
      const data = await response.json();
      setIssues([data, ...issues]);
      setShowCreateForm(false);
      setNewIssue({
        title: '',
        description: '',
        issue_type: 'RISK_FINDING',
        severity: 'MEDIUM',
        priority: 'P3',
        owner: '',
        app_name: ''
      });
      fetchStatistics();
    } catch (err) {
      console.error('Error creating issue:', err);
    }
  };

  const updateIssueStatus = async (issueId, newStatus) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(
        `${API_URL}/api/issue-management/${issueId}?user_id=${user?.id || 'user'}&user_name=${encodeURIComponent(user?.full_name || 'User')}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ status: newStatus })
        }
      );
      fetchIssues();
      fetchStatistics();
      if (selectedIssue?.id === issueId) {
        fetchIssueDetails(issueId);
      }
    } catch (err) {
      console.error('Error updating issue:', err);
    }
  };

  const addComment = async () => {
    if (!newComment.trim() || !selectedIssue) return;
    try {
      const token = localStorage.getItem('token');
      await fetch(
        `${API_URL}/api/issue-management/${selectedIssue.id}/comments?user_id=${user?.id || 'user'}&user_name=${encodeURIComponent(user?.full_name || 'User')}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ text: newComment, is_internal: false })
        }
      );
      setNewComment('');
      fetchIssueDetails(selectedIssue.id);
    } catch (err) {
      console.error('Error adding comment:', err);
    }
  };

  const syncToServiceNow = async (issueId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_URL}/api/issue-management/${issueId}/sync-servicenow?user_id=${user?.id || 'user'}&user_name=${encodeURIComponent(user?.full_name || 'User')}`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      const result = await response.json();
      if (result.servicenow_result?.success) {
        alert(`Synced to ServiceNow: ${result.servicenow_result.number}`);
        fetchIssueDetails(issueId);
      }
    } catch (err) {
      console.error('Error syncing to ServiceNow:', err);
    }
  };

  const getPriorityColor = (priority) => {
    const colors = { 'P1': 'bg-red-600', 'P2': 'bg-orange-500', 'P3': 'bg-yellow-500', 'P4': 'bg-green-500' };
    return colors[priority] || 'bg-gray-500';
  };

  const getStatusColor = (status) => {
    const colors = {
      'OPEN': 'bg-blue-600',
      'IN_PROGRESS': 'bg-yellow-600',
      'PENDING_REVIEW': 'bg-purple-600',
      'RESOLVED': 'bg-green-600',
      'CLOSED': 'bg-gray-600',
      'DEFERRED': 'bg-slate-600'
    };
    return colors[status] || 'bg-gray-500';
  };

  if (loading) {
    return <div className="p-6 bg-slate-900 min-h-screen text-white">Loading...</div>;
  }

  return (
    <div className="p-6 bg-slate-900 min-h-screen" data-testid="issue-management-page">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-white">Issue Management</h1>
            <p className="text-slate-400">Track and manage risk findings, control deficiencies, and compliance issues</p>
          </div>
          <Button onClick={() => setShowCreateForm(true)} data-testid="new-issue-btn">
            Create Issue
          </Button>
        </div>

        {/* Statistics Cards */}
        {statistics && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-white">{statistics.total}</div>
                <div className="text-xs text-slate-400">Total</div>
              </CardContent>
            </Card>
            <Card className="bg-blue-900/30 border-blue-700">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-blue-400">{statistics.open}</div>
                <div className="text-xs text-slate-400">Open</div>
              </CardContent>
            </Card>
            <Card className="bg-yellow-900/30 border-yellow-700">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-yellow-400">{statistics.in_progress}</div>
                <div className="text-xs text-slate-400">In Progress</div>
              </CardContent>
            </Card>
            <Card className="bg-green-900/30 border-green-700">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-green-400">{statistics.resolved}</div>
                <div className="text-xs text-slate-400">Resolved</div>
              </CardContent>
            </Card>
            <Card className="bg-red-900/30 border-red-700">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-red-400">{statistics.p1}</div>
                <div className="text-xs text-slate-400">P1 Critical</div>
              </CardContent>
            </Card>
            <Card className="bg-orange-900/30 border-orange-700">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-orange-400">{statistics.p2}</div>
                <div className="text-xs text-slate-400">P2 High</div>
              </CardContent>
            </Card>
            <Card className="bg-yellow-900/30 border-yellow-700">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-yellow-400">{statistics.p3}</div>
                <div className="text-xs text-slate-400">P3 Medium</div>
              </CardContent>
            </Card>
            <Card className="bg-green-900/30 border-green-700">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-green-400">{statistics.p4}</div>
                <div className="text-xs text-slate-400">P4 Low</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-4 flex-wrap">
          <Select value={filters.status || "all"} onValueChange={(v) => setFilters({...filters, status: v === "all" ? "" : v})}>
            <SelectTrigger className="w-40 bg-slate-800 border-slate-700">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="OPEN">Open</SelectItem>
              <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
              <SelectItem value="PENDING_REVIEW">Pending Review</SelectItem>
              <SelectItem value="RESOLVED">Resolved</SelectItem>
              <SelectItem value="CLOSED">Closed</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filters.priority || "all"} onValueChange={(v) => setFilters({...filters, priority: v === "all" ? "" : v})}>
            <SelectTrigger className="w-40 bg-slate-800 border-slate-700">
              <SelectValue placeholder="Priority" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Priorities</SelectItem>
              <SelectItem value="P1">P1 - Critical</SelectItem>
              <SelectItem value="P2">P2 - High</SelectItem>
              <SelectItem value="P3">P3 - Medium</SelectItem>
              <SelectItem value="P4">P4 - Low</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filters.type || "all"} onValueChange={(v) => setFilters({...filters, type: v === "all" ? "" : v})}>
            <SelectTrigger className="w-48 bg-slate-800 border-slate-700">
              <SelectValue placeholder="Issue Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="RISK_FINDING">Risk Finding</SelectItem>
              <SelectItem value="CONTROL_DEFICIENCY">Control Deficiency</SelectItem>
              <SelectItem value="COMPLIANCE_GAP">Compliance Gap</SelectItem>
              <SelectItem value="VULNERABILITY">Vulnerability</SelectItem>
              <SelectItem value="AUDIT_FINDING">Audit Finding</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Create Issue Form */}
        {showCreateForm && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Create New Issue</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="text-sm text-slate-400">Title *</label>
                  <Input
                    value={newIssue.title}
                    onChange={(e) => setNewIssue({...newIssue, title: e.target.value})}
                    className="bg-slate-700 border-slate-600"
                    placeholder="Issue title"
                  />
                </div>
                <div className="col-span-2">
                  <label className="text-sm text-slate-400">Description *</label>
                  <textarea
                    value={newIssue.description}
                    onChange={(e) => setNewIssue({...newIssue, description: e.target.value})}
                    className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="text-sm text-slate-400">Type</label>
                  <Select value={newIssue.issue_type} onValueChange={(v) => setNewIssue({...newIssue, issue_type: v})}>
                    <SelectTrigger className="bg-slate-700 border-slate-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="RISK_FINDING">Risk Finding</SelectItem>
                      <SelectItem value="CONTROL_DEFICIENCY">Control Deficiency</SelectItem>
                      <SelectItem value="COMPLIANCE_GAP">Compliance Gap</SelectItem>
                      <SelectItem value="VULNERABILITY">Vulnerability</SelectItem>
                      <SelectItem value="AUDIT_FINDING">Audit Finding</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-slate-400">Priority</label>
                  <Select value={newIssue.priority} onValueChange={(v) => setNewIssue({...newIssue, priority: v})}>
                    <SelectTrigger className="bg-slate-700 border-slate-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="P1">P1 - Critical</SelectItem>
                      <SelectItem value="P2">P2 - High</SelectItem>
                      <SelectItem value="P3">P3 - Medium</SelectItem>
                      <SelectItem value="P4">P4 - Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-slate-400">Owner</label>
                  <Input
                    value={newIssue.owner}
                    onChange={(e) => setNewIssue({...newIssue, owner: e.target.value})}
                    className="bg-slate-700 border-slate-600"
                    placeholder="owner@company.com"
                  />
                </div>
                <div>
                  <label className="text-sm text-slate-400">Application</label>
                  <Input
                    value={newIssue.app_name}
                    onChange={(e) => setNewIssue({...newIssue, app_name: e.target.value})}
                    className="bg-slate-700 border-slate-600"
                    placeholder="Application name"
                  />
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowCreateForm(false)}>Cancel</Button>
                <Button onClick={createIssue} disabled={!newIssue.title || !newIssue.description}>Create Issue</Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Issue Detail Panel */}
        {selectedIssue && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-white">{selectedIssue.issue_id}: {selectedIssue.title}</CardTitle>
              <Button variant="ghost" onClick={() => setSelectedIssue(null)}>Close</Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2 flex-wrap">
                <span className={`px-2 py-1 rounded text-xs text-white ${getPriorityColor(selectedIssue.priority)}`}>
                  {selectedIssue.priority}
                </span>
                <span className={`px-2 py-1 rounded text-xs text-white ${getStatusColor(selectedIssue.status)}`}>
                  {selectedIssue.status}
                </span>
                <span className="px-2 py-1 rounded text-xs bg-slate-600">{selectedIssue.type}</span>
                {selectedIssue.servicenow?.synced && (
                  <span className="px-2 py-1 rounded text-xs bg-purple-600">
                    ServiceNow: {selectedIssue.servicenow.incident_number}
                  </span>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-slate-400">Source:</span> <span className="text-white">{selectedIssue.source}</span></div>
                <div><span className="text-slate-400">Owner:</span> <span className="text-white">{selectedIssue.owner || 'Unassigned'}</span></div>
                <div><span className="text-slate-400">Application:</span> <span className="text-white">{selectedIssue.app_name || 'N/A'}</span></div>
                <div><span className="text-slate-400">Due Date:</span> <span className="text-white">{selectedIssue.due_date || 'N/A'}</span></div>
              </div>
              
              <div>
                <h4 className="text-slate-400 text-sm mb-1">Description</h4>
                <p className="text-white">{selectedIssue.description}</p>
              </div>

              {/* Actions */}
              <div className="flex gap-2 flex-wrap">
                {selectedIssue.status === 'OPEN' && (
                  <Button size="sm" onClick={() => updateIssueStatus(selectedIssue.id, 'IN_PROGRESS')}>
                    Start Work
                  </Button>
                )}
                {selectedIssue.status === 'IN_PROGRESS' && (
                  <Button size="sm" onClick={() => updateIssueStatus(selectedIssue.id, 'RESOLVED')}>
                    Mark Resolved
                  </Button>
                )}
                {selectedIssue.status === 'RESOLVED' && (
                  <Button size="sm" onClick={() => updateIssueStatus(selectedIssue.id, 'CLOSED')}>
                    Close Issue
                  </Button>
                )}
                {!selectedIssue.servicenow?.synced && (
                  <Button size="sm" variant="outline" onClick={() => syncToServiceNow(selectedIssue.id)}>
                    Sync to ServiceNow
                  </Button>
                )}
              </div>

              {/* History */}
              <div>
                <h4 className="text-slate-400 text-sm mb-2">History</h4>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {selectedIssue.history?.slice().reverse().map((entry, idx) => (
                    <div key={idx} className="text-xs bg-slate-700/50 p-2 rounded">
                      <span className="text-slate-400">{new Date(entry.timestamp).toLocaleString()}</span>
                      <span className="text-white ml-2">{entry.user_name}: {entry.action}</span>
                      {entry.details && <span className="text-slate-400 ml-1">- {entry.details}</span>}
                    </div>
                  ))}
                </div>
              </div>

              {/* Comments */}
              <div>
                <h4 className="text-slate-400 text-sm mb-2">Comments</h4>
                <div className="space-y-2 max-h-40 overflow-y-auto mb-2">
                  {selectedIssue.comments?.map((comment) => (
                    <div key={comment.id} className="bg-slate-700/50 p-2 rounded">
                      <div className="text-xs text-slate-400">
                        {comment.user_name} - {new Date(comment.created_at).toLocaleString()}
                      </div>
                      <div className="text-sm text-white">{comment.text}</div>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Add a comment..."
                    className="bg-slate-700 border-slate-600"
                  />
                  <Button size="sm" onClick={addComment}>Add</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Issues List */}
        <div className="space-y-2">
          {issues.map((issue) => (
            <Card 
              key={issue.id} 
              className="bg-slate-800/50 border-slate-700 cursor-pointer hover:bg-slate-800"
              onClick={() => fetchIssueDetails(issue.id)}
            >
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-xs text-white ${getPriorityColor(issue.priority)}`}>
                        {issue.priority}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-xs text-white ${getStatusColor(issue.status)}`}>
                        {issue.status}
                      </span>
                      <span className="text-sm font-medium text-white">{issue.issue_id}</span>
                    </div>
                    <h3 className="text-white">{issue.title}</h3>
                    <div className="flex gap-4 text-xs text-slate-500">
                      <span>{issue.type}</span>
                      <span>Source: {issue.source}</span>
                      {issue.app_name && <span>App: {issue.app_name}</span>}
                      <span>Due: {issue.due_date || 'N/A'}</span>
                    </div>
                  </div>
                  {issue.servicenow?.synced && (
                    <span className="text-xs bg-purple-600 px-2 py-1 rounded">
                      {issue.servicenow.incident_number}
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
          
          {issues.length === 0 && (
            <div className="text-center py-12 text-slate-500">
              No issues found. Adjust filters or create a new issue.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IssueManagement;
