import {
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogContent,
  Divider,
  IconButton,
  Paper,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';
import logoFull from './assets/logo-full.webp';
import { zillowService } from './services/zillowService';

interface PropertyPopupProps {
  zpid: string | null;
  isOpen: boolean;
  onClose: () => void;
  viewOnMarketUrl?: string;
  onSentAndClose?: (id: string | number) => void;
}

interface PropertyData {
  zpid: string;
  address: string;
  city: string;
  state: string;
  zipcode: string;
  price: number;
  beds: number;
  baths: number;
  living_area: number;
  year_built?: number;
  lot_area_value?: number;
  lot_area_units?: string;
  home_type?: string;
  home_status?: string;
  description?: string;
  images: string[];
  tax_history?: { year: number; tax_paid: number; value: number }[];
  zestimate?: number;
  hoa?: number;
  price_change?: string;
  listingAgent?: {
    name: string;
    license: string;
    email: string;
    phone: string;
    brokerage?: string;
  };
  [key: string]: any;
}

export default function PropertyPopup({ zpid, isOpen, onClose, viewOnMarketUrl, onSentAndClose }: PropertyPopupProps) {
  const [property, setProperty] = useState<PropertyData | null>(null); 
  const [loadingSend, setLoadingSend] = useState(false);
  const [showGlobalLoading, setShowGlobalLoading] = useState(false);
  const [resultDialog, setResultDialog] = useState<{ open: boolean; success: boolean; message: string }>({ open: false, success: false, message: '' });

  const fetchProperty = () => {
    if (isOpen && zpid) { 
      fetch(`/api/zillow/property/${zpid}`)
        .then(res => res.json())
        .then(data => {
          if (!data.success) { 
            setProperty(null);
          } else {
            setProperty(data); 
          } 
        })
        .catch(() => { 
          setProperty(null); 
        });
    } else {
      setProperty(null); 
    }
  };

  const handleSendToCyclSales = async () => {
    if (!property?.id && !property?.zpid) return;
    setLoadingSend(true);
    setShowGlobalLoading(true);
    let success = false;
    let message = '';
    try {
      const id = property.id ? Number(property.id) : Number(property.zpid);
      const result = await zillowService.sendToCyclSales([id]);
      if (result.success) {
        success = true;
        message = 'Sent to Cycl Sales!';
      } else {
        message = result.error || 'Failed to send to Cycl Sales';
      }
    } catch (err: any) {
      message = err.message || 'Failed to send to Cycl Sales';
    }
    // Always show loading for at least 3 seconds
    setTimeout(() => {
      setShowGlobalLoading(false);
      setResultDialog({ open: true, success, message });
      setLoadingSend(false);
    }, 3000);
  };

  const handleClose = () => {
    if (resultDialog.open && resultDialog.success && property) {
      if (onSentAndClose) {
        onSentAndClose(property.id || property.zpid);
      }
    }
    onClose();
  };

  useEffect(() => {
    fetchProperty();
    // eslint-disable-next-line
  }, [zpid, isOpen]); 

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      maxWidth={false}
      PaperProps={{
        sx: {
          width: '1200px',
          maxWidth: '98vw',
          height: '96vh',
          maxHeight: '96vh',
          borderRadius: 5,
          boxShadow: 8,
          bgcolor: '#fff',
          p: 0,
          overflow: 'visible',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        },
      }}
    >
      <DialogContent sx={{ p: 0, position: 'relative', bgcolor: '#fff', height: '100%', overflow: 'auto' }}>
        {/* Loading overlay */}
        {showGlobalLoading && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              bgcolor: 'rgba(34,34,34,0.8)',
              zIndex: 1300,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center', 
            }}
          >
            <CircularProgress size={72} thickness={5} color="inherit" sx={{ color: '#fff' }} />
          </Box>
        )}
        {/* Result dialog replaces content after send */}
        {resultDialog.open ? (
          <Box sx={{ width: '100%', height: 500, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 3 }}>
            <Typography variant="h4" sx={{ color: resultDialog.success ? '#22c55e' : '#ef4444', fontWeight: 700, mb: 2 }}>
              {resultDialog.success ? 'Success!' : 'Error'}
            </Typography>
            <Typography variant="h6" sx={{ color: '#222', mb: 3 }}>{resultDialog.message}</Typography>
            <Button variant="contained" color="primary" onClick={handleClose} sx={{ fontSize: 18, borderRadius: 2, px: 4, py: 1 }}>
              Close
            </Button>
          </Box>
        ) : (
          <>
            {/* Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: 3, pt: 2, pb: 0 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <IconButton onClick={onClose} sx={{ p: 0, mr: 1 }}>
                  <svg width="28" height="28" fill="none" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6" stroke="#222" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
                </IconButton>
                <Typography variant="body2" sx={{ color: '#222', fontWeight: 500, cursor: 'pointer', fontSize: 18 }}>Back to search</Typography>
              </Box>
              <Box sx={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
                <Box component="img" src={logoFull} alt="Zillow" sx={{ height: 36 }} />
              </Box>
              <Box sx={{ width: 120 }} /> {/* Spacer for symmetry */}
            </Box>
            {/* Main content layout */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4, px: 3, pt: 1, pb: 3, alignItems: 'flex-start', height: 'calc(100% - 70px)' }}>
              {/* Left: Images above details */}
              <Box sx={{ flex: 2.5, minWidth: 0, display: 'flex', flexDirection: 'column', height: '100%' }}>
                {/* Image gallery: main image and 4 thumbnails in a single row, no gaps */}
                <Box sx={{ display: 'flex', gap: 0, flex: 2.5, mb: 2, borderRadius: 3, overflow: 'hidden', height: 400, minHeight: 400 }}>
                  <Box sx={{ flex: 2.5, minWidth: 0, height: '100%' }}>
                    {property?.images?.[0] && (
                      <Box component="img" src={property.images[0]} alt="Main" sx={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
                    )}
                  </Box>
                  <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, height: '100%' }}>
                    {[1, 2, 3, 4].map((idx) => (
                      property?.images?.[idx] ? (
                        <Box key={idx} component="img" src={property.images[idx]} alt={`Preview ${idx + 1}`} sx={{ width: '100%', height: '25%', objectFit: 'cover', display: 'block' }} />
                      ) : (
                        <Box key={idx} sx={{ width: '100%', height: '25%', bgcolor: '#f5f6fa' }} />
                      )
                    ))}
                  </Box>
                </Box>
                {/* Details below image gallery */}
                <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'flex-start' }}>

                  {/* Listing Provided by */}
                  <Typography variant="body2" sx={{ color: '#555', mb: 0.5, mt: 1, fontSize: 15 }}>
                    Listing Provided by:
                  </Typography>
                  {/* Price cut */}
                  {property?.price_change && (
                    <Box sx={{ bgcolor: '#f8d7da', color: '#b91c1c', fontWeight: 700, fontSize: 15, borderRadius: 1, px: 1.5, py: 0.5, mb: 1, mt: 0.5 }}>
                      Price cut: {property.price_change}
                    </Box>
                  )}

                  <Box sx={{ display: 'flex', flexDirection: 'row', gap: 2, mb: 2 }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 2 }}>
                      {/* Price and address */}
                      <Typography variant="h3" sx={{ fontWeight: 700, color: '#222', mb: 0.5, fontSize: 38, lineHeight: 1.1 }}>
                        {property?.price ? `$${property.price.toLocaleString()}` : '--'}
                      </Typography>
                      <Typography variant="h6" sx={{ color: '#222', fontWeight: 400, mb: 1, fontSize: 20, lineHeight: 1.2 }}>
                        {property?.address}, {property?.city}, {property?.state} {property?.zipcode}
                      </Typography>
                      {/* Monthly estimate bar */}
                      <Box sx={{ display: 'flex', alignItems: 'center', bgcolor: '#f1f6fb', borderRadius: 2, px: 2, py: 1, width: 'fit-content', mb: 2 }}>
                        <Typography variant="subtitle1" sx={{ color: '#2563eb', fontWeight: 400, mr: 1 }}>Listing Provided by:</Typography>
                        <Box>
                          <Typography variant="body2" sx={{ color: '#2563eb', fontWeight: 600, cursor: 'pointer', fontSize: 18 }}>
                            {property?.listingAgent?.name ?? '--'}
                            {property?.listingAgent?.license ? ` ${property.listingAgent.license}` : ''}
                          </Typography>
                          {property?.listingAgent?.email && (
                            <Typography variant="body2" sx={{ color: '#666', fontSize: 14 }}>
                              Email: {property.listingAgent.email}
                            </Typography>
                          )}
                          {property?.listingAgent?.phone && (
                            <Typography variant="body2" sx={{ color: '#666', fontSize: 14 }}>
                              Phone: {property.listingAgent.phone}
                            </Typography>
                          )}
                          {property?.listingAgent?.brokerage && (
                            <Typography variant="body2" sx={{ color: '#666', fontSize: 14 }}>
                              Brokerage: {property.listingAgent.brokerage}
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    </Box>

                    {/* Summary facts row */}
                    <Box sx={{ display: 'flex', gap: 8, alignItems: 'center', mb: 2, mt: 2 }}>
                      <Box sx={{ textAlign: 'center', minWidth: 80 }}>
                        <Typography variant="h4" sx={{ fontWeight: 700, fontSize: 32 }}>{property?.beds ? property.beds : '--'}</Typography>
                        <Typography variant="body2" sx={{ color: '#555', fontSize: 18 }}>beds</Typography>
                      </Box>
                      <Box sx={{ textAlign: 'center', minWidth: 80 }}>
                        <Typography variant="h4" sx={{ fontWeight: 700, fontSize: 32 }}>{property?.baths ? property.baths : '--'}</Typography>
                        <Typography variant="body2" sx={{ color: '#555', fontSize: 18 }}>baths</Typography>
                      </Box>
                      <Box sx={{ textAlign: 'center', minWidth: 80 }}>
                        <Typography variant="h4" sx={{ fontWeight: 700, fontSize: 32 }}>{property?.living_area?.toLocaleString() ?? '--'}</Typography>
                        <Typography variant="body2" sx={{ color: '#555', fontSize: 18 }}>sqft</Typography>
                      </Box>
                    </Box>

                    <Paper elevation={0} variant='outlined' sx={{ width: '100%', maxWidth: 300, borderRadius: 2, p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                      <Button
                        variant="contained"
                        size='small'
                        sx={{ bgcolor: '#2563eb', color: '#fff', borderRadius: 2, height: 44, fontSize: 16, width: '100%', textTransform: 'none', boxShadow: 'none', '&:hover': { bgcolor: '#1742a0' } }}
                        onClick={handleSendToCyclSales}
                        disabled={loadingSend}
                        startIcon={loadingSend ? <CircularProgress size={20} color="inherit" /> : null}
                      >
                        {loadingSend ? 'Sending...' : 'Send to Cycl Sales'}
                      </Button>

                      {viewOnMarketUrl && (
                        <Button
                          variant="outlined" size='small' sx={{ mt: 2, bgcolor: '#fff', borderRadius: 2, height: 44, fontSize: 16, width: '100%', textTransform: 'none', boxShadow: 'none', '&:hover': { bgcolor: '#1742a0', color: '#fff' } }}
                          onClick={() => window.open(viewOnMarketUrl, '_blank')}
                        >
                          View on Market
                        </Button>
                      )}
                    </Paper>
                  </Box>

                  {/* Secondary facts grid: 2 rows of 3, card style, icons */}
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
                    <Paper elevation={0} sx={{ flex: '1 1 30%', bgcolor: '#f7f8fa', borderRadius: 2, p: 1, display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Box component="span" sx={{ mr: 1, color: '#888', fontSize: 22 }}>🏠</Box>
                      <Typography sx={{ fontSize: 17 }}>{property?.home_type}</Typography>
                    </Paper>
                    <Paper elevation={0} sx={{ flex: '1 1 30%', bgcolor: '#f7f8fa', borderRadius: 2, p: 1, display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Box component="span" sx={{ mr: 1, color: '#888', fontSize: 22 }}>🏗️</Box>
                      <Typography sx={{ fontSize: 17 }}>Built in {property?.year_built ? property.year_built : '--'}</Typography>
                    </Paper>
                    <Paper elevation={0} sx={{ flex: '1 1 30%', bgcolor: '#f7f8fa', borderRadius: 2, p: 1, display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Box component="span" sx={{ mr: 1, color: '#888', fontSize: 22 }}>📏</Box>
                      <Typography sx={{ fontSize: 17 }}>{property?.lot_area_value ? `${property.lot_area_value.toLocaleString()} ${property.lot_area_units}` : '--'} {property?.lot_area_units === 'ac' ? 'acres' : 'sqft'}</Typography>
                    </Paper>
                    <Paper elevation={0} sx={{ flex: '1 1 30%', bgcolor: '#f7f8fa', borderRadius: 2, p: 1, display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Box component="span" sx={{ mr: 1, color: '#888', fontSize: 22 }}>💲</Box>
                      <Typography sx={{ fontSize: 17 }}>{property?.zestimate ? property.zestimate.toLocaleString() : '--'} Zestimate®</Typography>
                    </Paper>
                    <Paper elevation={0} sx={{ flex: '1 1 30%', bgcolor: '#f7f8fa', borderRadius: 2, p: 1, display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Box component="span" sx={{ mr: 1, color: '#888', fontSize: 22 }}>💲</Box>
                      <Typography sx={{ fontSize: 17 }}>$372/sqft</Typography>
                    </Paper>
                    <Paper elevation={0} sx={{ flex: '1 1 30%', bgcolor: '#f7f8fa', borderRadius: 2, p: 1, display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Box component="span" sx={{ mr: 1, color: '#888', fontSize: 22 }}>🏢</Box>
                      <Typography sx={{ fontSize: 17 }}>$-- HOA</Typography>
                    </Paper>
                  </Box>
                  <Divider sx={{ width: '100%', my: 2 }} />
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#222', mb: 0.5, fontSize: 38, lineHeight: 1.1 }}>
                    Description
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#222', fontSize: 16, lineHeight: 1.5, mb: 10 }}>
                    {property?.description}
                  </Typography>
                </Box>
              </Box>
            </Box>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
} 