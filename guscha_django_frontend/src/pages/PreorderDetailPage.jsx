import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import DetailPage from './DetailPage';

const PreorderDetailPage = () => {
  const { id } = useParams();
  const [preorder, setPreorder] = useState(null);
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    const abortController = new AbortController();
    
    const fetchPreorder = async () => {
      setStatus('loading');
      try {
        const response = await fetch(`/api/products/preorders/${id}/`, {
          signal: abortController.signal
        });
        if (!response.ok) throw new Error('Preorder not found');
        const data = await response.json();
        setPreorder(data);
        setStatus('success');
      } catch (error) {
        if (error.name === 'AbortError') return;
        setStatus('error');
      }
    };
    fetchPreorder();
    
    return () => abortController.abort();
  }, [id]);

  if (status === 'loading') return <div className="pdp-status">Loading...</div>;
  if (status === 'error') return <div className="pdp-status">Preorder not found.</div>;

  return <DetailPage item={preorder} itemType="preorder" />;
};

export default PreorderDetailPage;