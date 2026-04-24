import { useState, useEffect } from 'react';
import { api } from '@/App';

const KnowledgeGraph = ({ user }) => {
  const [graphData, setGraphData] = useState({ entities: [], relations: [] });
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadGraph();
  }, [filterType]);

  const loadGraph = async () => {
    try {
      const params = filterType !== 'all' ? { entity_type: filterType } : {};
      const response = await api.get('/knowledge-graph', { params });
      setGraphData(response.data);
    } catch (error) {
      console.error('Failed to load knowledge graph:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery) return;
    
    try {
      const response = await api.get('/knowledge-graph/query', {
        params: { entity_name: searchQuery, depth: 2 }
      });
      
      setSelectedEntity(response.data.root_entity);
      setGraphData({
        entities: [response.data.root_entity, ...response.data.related_entities],
        relations: response.data.relations
      });
    } catch (error) {
      console.error('Failed to query knowledge graph:', error);
    }
  };

  const getEntityColor = (type) => {
    const colors = {
      'SYSTEM': '#3b82f6',
      'RISK': '#ef4444',
      'CONTROL': '#10b981',
      'REGULATION': '#8b5cf6',
      'BUSINESS_UNIT': '#f59e0b',
      'PERSON': '#ec4899',
      'VENDOR': '#06b6d4',
      'ASSET': '#6366f1'
    };
    return colors[type] || '#6b7280';
  };

  const getRelationColor = (type) => {
    const colors = {
      'MITIGATES': '#10b981',
      'AFFECTS': '#ef4444',
      'IMPLEMENTS': '#3b82f6',
      'OWNED_BY': '#8b5cf6',
      'REQUIRES': '#f59e0b',
      'DEPENDS_ON': '#ec4899',
      'MONITORS': '#06b6d4',
      'COMPLIES_WITH': '#6366f1'
    };
    return colors[type] || '#6b7280';
  };

  if (loading) {
    return (
      <div className="page-content">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div data-testid="knowledge-graph-page">
      <div className="page-header">
        <h1 className="page-title" data-testid="kg-title">Organizational Knowledge Graph</h1>
        <p className="page-subtitle">AI-powered contextual understanding of your organization</p>
      </div>

      <div className="page-content">
        {/* Search and Filter */}
        <div className="card mb-6">
          <div className="grid grid-2 gap-4">
            <div>
              <label className="form-label">Search Entity</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  className="form-input"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by name (e.g., AWS Production, MFA, NIST)..."
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  data-testid="search-input"
                />
                <button className="btn btn-primary" onClick={handleSearch} data-testid="search-button">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="M21 21l-4.35-4.35"></path>
                  </svg>
                  Search
                </button>
              </div>
            </div>
            <div>
              <label className="form-label">Filter by Type</label>
              <select
                className="form-select"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                data-testid="filter-type"
              >
                <option value="all">All Types</option>
                <option value="SYSTEM">Systems</option>
                <option value="RISK">Risks</option>
                <option value="CONTROL">Controls</option>
                <option value="REGULATION">Regulations</option>
                <option value="BUSINESS_UNIT">Business Units</option>
                <option value="VENDOR">Vendors</option>
                <option value="ASSET">Assets</option>
              </select>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-3 mb-6">
          <div className="stat-card">
            <div className="stat-label">Total Entities</div>
            <div className="stat-value">{graphData.entities.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Total Relations</div>
            <div className="stat-value">{graphData.relations.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Knowledge Density</div>
            <div className="stat-value" style={{ fontSize: '28px' }}>
              {graphData.entities.length > 0 ? (graphData.relations.length / graphData.entities.length).toFixed(1) : 0}
            </div>
          </div>
        </div>

        {/* Graph Visualization (Simplified List View) */}
        <div className="grid grid-2 gap-6">
          {/* Entities */}
          <div className="card" data-testid="entities-card">
            <h3 className="card-title mb-4">Entities ({graphData.entities.length})</h3>
            <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
              {graphData.entities.length > 0 ? (
                <div className="space-y-2">
                  {graphData.entities.map((entity) => (
                    <div
                      key={entity.id}
                      onClick={() => setSelectedEntity(entity)}
                      style={{
                        padding: '12px',
                        background: selectedEntity?.id === entity.id ? '#eff6ff' : '#f8fafc',
                        borderLeft: `4px solid ${getEntityColor(entity.entity_type)}`,
                        borderRadius: '6px',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                      data-testid={`entity-${entity.id}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div style={{ fontSize: '14px', fontWeight: '600', color: '#0f172a', marginBottom: '4px' }}>
                            {entity.name}
                          </div>
                          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>
                            {entity.description || 'No description'}
                          </div>
                        </div>
                        <span
                          style={{
                            padding: '4px 8px',
                            background: getEntityColor(entity.entity_type) + '20',
                            color: getEntityColor(entity.entity_type),
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontWeight: '600'
                          }}
                        >
                          {entity.entity_type}
                        </span>
                      </div>
                      {Object.keys(entity.properties || {}).length > 0 && (
                        <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
                          {Object.entries(entity.properties).slice(0, 3).map(([key, value]) => (
                            <span key={key} style={{ marginRight: '12px' }}>
                              {key}: {JSON.stringify(value)}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state" style={{ padding: '40px 20px' }}>
                  <p className="text-gray text-sm">No entities found</p>
                </div>
              )}
            </div>
          </div>

          {/* Relations */}
          <div className="card" data-testid="relations-card">
            <h3 className="card-title mb-4">Relations ({graphData.relations.length})</h3>
            <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
              {graphData.relations.length > 0 ? (
                <div className="space-y-2">
                  {graphData.relations.map((relation) => {
                    const sourceEntity = graphData.entities.find(e => e.id === relation.source_entity_id);
                    const targetEntity = graphData.entities.find(e => e.id === relation.target_entity_id);
                    
                    return (
                      <div
                        key={relation.id}
                        style={{
                          padding: '12px',
                          background: '#f8fafc',
                          borderRadius: '6px'
                        }}
                        data-testid={`relation-${relation.id}`}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
                          <span
                            style={{
                              padding: '4px 8px',
                              background: sourceEntity ? getEntityColor(sourceEntity.entity_type) + '20' : '#f1f5f9',
                              color: sourceEntity ? getEntityColor(sourceEntity.entity_type) : '#64748b',
                              borderRadius: '4px',
                              fontWeight: '600'
                            }}
                          >
                            {sourceEntity?.name || 'Unknown'}
                          </span>
                          <span style={{ fontSize: '10px', color: '#94a3b8' }}>→</span>
                          <span
                            style={{
                              padding: '4px 8px',
                              background: getRelationColor(relation.relation_type) + '20',
                              color: getRelationColor(relation.relation_type),
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: '600',
                              textTransform: 'uppercase'
                            }}
                          >
                            {relation.relation_type.replace('_', ' ')}
                          </span>
                          <span style={{ fontSize: '10px', color: '#94a3b8' }}>→</span>
                          <span
                            style={{
                              padding: '4px 8px',
                              background: targetEntity ? getEntityColor(targetEntity.entity_type) + '20' : '#f1f5f9',
                              color: targetEntity ? getEntityColor(targetEntity.entity_type) : '#64748b',
                              borderRadius: '4px',
                              fontWeight: '600'
                            }}
                          >
                            {targetEntity?.name || 'Unknown'}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="empty-state" style={{ padding: '40px 20px' }}>
                  <p className="text-gray text-sm">No relations found</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Selected Entity Detail */}
        {selectedEntity && (
          <div className="card mt-6" data-testid="selected-entity-detail">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="card-title" style={{ marginBottom: '8px' }}>{selectedEntity.name}</h3>
                <span
                  className="badge"
                  style={{
                    background: getEntityColor(selectedEntity.entity_type) + '20',
                    color: getEntityColor(selectedEntity.entity_type)
                  }}
                >
                  {selectedEntity.entity_type}
                </span>
              </div>
              <button
                className="btn btn-outline"
                onClick={() => setSelectedEntity(null)}
                style={{ fontSize: '13px', padding: '6px 12px' }}
              >
                Close
              </button>
            </div>

            {selectedEntity.description && (
              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>Description</div>
                <div style={{ fontSize: '14px', color: '#334155' }}>{selectedEntity.description}</div>
              </div>
            )}

            {Object.keys(selectedEntity.properties || {}).length > 0 && (
              <div>
                <div style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>Properties</div>
                <div className="grid grid-2 gap-3">
                  {Object.entries(selectedEntity.properties).map(([key, value]) => (
                    <div key={key} style={{ padding: '12px', background: '#f8fafc', borderRadius: '6px' }}>
                      <div style={{ fontSize: '11px', fontWeight: '600', color: '#64748b', marginBottom: '4px' }}>
                        {key.replace('_', ' ').toUpperCase()}
                      </div>
                      <div style={{ fontSize: '13px', color: '#0f172a' }}>
                        {Array.isArray(value) ? value.join(', ') : JSON.stringify(value)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Show connected relations */}
            <div className="mt-4">
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>Connected Relations</div>
              <div style={{ fontSize: '13px', color: '#64748b' }}>
                {graphData.relations.filter(
                  r => r.source_entity_id === selectedEntity.id || r.target_entity_id === selectedEntity.id
                ).length} relation(s)
              </div>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="card mt-6">
          <h3 className="card-title mb-4">Entity Types Legend</h3>
          <div className="grid grid-4 gap-3">
            {['SYSTEM', 'RISK', 'CONTROL', 'REGULATION', 'BUSINESS_UNIT', 'VENDOR', 'ASSET'].map((type) => (
              <div key={type} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div
                  style={{
                    width: '16px',
                    height: '16px',
                    background: getEntityColor(type),
                    borderRadius: '4px'
                  }}
                ></div>
                <span style={{ fontSize: '13px', color: '#334155' }}>{type.replace('_', ' ')}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraph;
