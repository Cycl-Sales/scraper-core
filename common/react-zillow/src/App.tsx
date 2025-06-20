import { ArrowDownward, ArrowUpward } from '@mui/icons-material';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import SearchIcon from '@mui/icons-material/Search';
import SendIcon from '@mui/icons-material/Send';
import type { SelectChangeEvent } from '@mui/material';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  createTheme,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  IconButton,
  InputAdornment,
  Menu,
  MenuItem,
  OutlinedInput,
  Pagination,
  Paper,
  Radio,
  RadioGroup,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  ThemeProvider,
  Typography
} from '@mui/material';
import Skeleton from '@mui/material/Skeleton';
import React, { useCallback, useEffect, useState } from 'react';
import PropertyPopup from './PropertyPopup';
import type { ZillowProperty } from './services/zillowService';
import { api, zillowService } from './services/zillowService';

const theme = createTheme({
  palette: {
    mode: 'light',
    background: {
      default: '#f5f6fa',
      paper: '#fff',
    },
  },
});

// Add useDebounce hook at the top level
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

// New: FilterSummaryDialog component
function FilterSummaryDialog({
  open,
  onClose,
  onContinue,
  filters
}: {
  open: boolean,
  onClose: () => void,
  onContinue: () => void,
  filters: Record<string, any>
}) {
  // Helper to format filter values
  const formatValue = (val: any) => {
    if (Array.isArray(val)) return val.join(', ');
    if (typeof val === 'boolean') return val ? 'Yes' : 'No';
    if (val === '' || val === undefined || val === null) return 'Any';
    return val;
  };
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Current Filter Selections</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 1 }}>You are about to search the market with these filters:</Typography>
          <Box component="ul" sx={{ pl: 3, mb: 0 }}>
            {Object.entries(filters).map(([key, value]) => (
              <li key={key}>
                <Typography variant="body1">
                  <strong>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> {formatValue(value)}
                </Typography>
              </li>
            ))}
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="secondary">Cancel</Button>
        <Button onClick={onContinue} color="primary" variant="contained">Continue Search</Button>
      </DialogActions>
    </Dialog>
  );
}

function App() {
  const [properties, setProperties] = useState<ZillowProperty[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [selectedProperties, setSelectedProperties] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const [priceAnchorEl, setPriceAnchorEl] = useState<null | HTMLElement>(null);
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [listingTypeAnchorEl, setListingTypeAnchorEl] = useState<null | HTMLElement>(null);
  const [listingTypeValue, setListingTypeValue] = useState<'for_sale' | 'for_rent' | 'sold'>('for_sale');
  const [bedsBathsAnchorEl, setBedsBathsAnchorEl] = useState<null | HTMLElement>(null);
  const [bedrooms, setBedrooms] = useState('');
  const [bathrooms, setBathrooms] = useState('');
  const [exactMatch, setExactMatch] = useState(false);
  const bedroomOptions = ['', '1', '2', '3', '4', '5'];
  const bathroomOptions = ['', '1', '1.5', '2', '3', '4'];
  const [homeTypeAnchorEl, setHomeTypeAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedHomeTypes, setSelectedHomeTypes] = useState<string[]>([
    'SINGLE_FAMILY',
    'TOWNHOUSE',
    'MULTI_FAMILY',
    'CONDO',
    'LOT',
    'APARTMENT',
    'MANUFACTURED',
  ]);
  const homeTypeOptions = [
    { value: 'SINGLE_FAMILY', label: 'Houses' },
    { value: 'TOWNHOUSE', label: 'Townhomes' },
    { value: 'MULTI_FAMILY', label: 'Multi-family' },
    { value: 'CONDO', label: 'Condos/Co-ops' },
    { value: 'LOT', label: 'Lots/Land' },
    { value: 'APARTMENT', label: 'Apartments' },
    { value: 'MANUFACTURED', label: 'Manufactured' },
  ];
  const [moreAnchorEl, setMoreAnchorEl] = useState<null | HTMLElement>(null);
  const [sqftMin, setSqftMin] = useState('');
  const [sqftMax, setSqftMax] = useState('');
  const [lotMin, setLotMin] = useState('');
  const [lotMax, setLotMax] = useState('');
  const [yearMin, setYearMin] = useState('');
  const [yearMax, setYearMax] = useState('');
  const [hasBasement, setHasBasement] = useState(false);
  const [tour3D, setTour3D] = useState(false);
  const [instantTour, setInstantTour] = useState(false);
  const [allowsLargeDogs, setAllowsLargeDogs] = useState(false);
  const [allowsSmallDogs, setAllowsSmallDogs] = useState(false);
  const [allowsCats, setAllowsCats] = useState(false);
  const [noPets, setNoPets] = useState(false);
  const [mustHaveAC, setMustHaveAC] = useState(false);
  const [mustHavePool, setMustHavePool] = useState(false);
  const [waterfront, setWaterfront] = useState(false);
  const [onSiteParking, setOnSiteParking] = useState(false);
  const [inUnitLaundry, setInUnitLaundry] = useState(false);
  const [acceptsZillowApps, setAcceptsZillowApps] = useState(false);
  const [incomeRestricted, setIncomeRestricted] = useState(false);
  const [hardwoodFloors, setHardwoodFloors] = useState(false);
  const [disabledAccess, setDisabledAccess] = useState(false);
  const [utilitiesIncluded, setUtilitiesIncluded] = useState(false);
  const [shortTermLease, setShortTermLease] = useState(false);
  const [furnished, setFurnished] = useState(false);
  const [outdoorSpace, setOutdoorSpace] = useState(false);
  const [controlledAccess, setControlledAccess] = useState(false);
  const [highSpeedInternet, setHighSpeedInternet] = useState(false);
  const [elevator, setElevator] = useState(false);
  const [apartmentCommunity, setApartmentCommunity] = useState(false);
  const [viewCity, setViewCity] = useState(false);
  const [viewMountain, setViewMountain] = useState(false);
  const [viewPark, setViewPark] = useState(false);
  const [viewWater, setViewWater] = useState(false);
  const [commute, setCommute] = useState('');
  const [daysOnZillow, setDaysOnZillow] = useState('');
  const [keywords, setKeywords] = useState('');
  const [fiftyFivePlus, setFiftyFivePlus] = useState('include');
  const [sortColumn, setSortColumn] = useState<string>('street_address');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [pageSize, setPageSize] = useState(10);
  const pageSizeOptions = [10, 20, 50];
  const [dataSource, setDataSource] = useState<'db' | 'market'>('db');
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedZpid, setSelectedZpid] = useState<string | null>(null);
  const [filteredProperties, setFilteredProperties] = useState<ZillowProperty[]>([]);
  const [showSendToCyclSalesPopup, setShowSendToCyclSalesPopup] = useState(false);
  const [loadingSendToCS, setLoadingSendToCS] = useState(false);
  const [fadingProperties, setFadingProperties] = useState<Set<string>>(new Set());
  const [locationId, setLocationId] = useState<string | null>(null);
  const [showFilterSummary, setShowFilterSummary] = useState(false);
  const [backgroundFetching, setBackgroundFetching] = useState(false);

  const sqftOptions = ['', '500', '750', '1000', '1250', '1500', '1750', '2000', '2250', '2500', '2750', '3000', '3500', '4000', '5000', '7500'];
  const lotOptions = ['', '1000', '2000', '3000', '4000', '5000', '7500', '10890', '21780', '43560', '87120', '217800', '435600', '871200', '2178000', '4356000'];
  const lotLabels = ['', '1,000 sqft', '2,000 sqft', '3,000 sqft', '4,000 sqft', '5,000 sqft', '7,500 sqft', '1/4 acre/10,890 sqft', '1/2 acre', '1 acre', '2 acres', '5 acres', '10 acres', '20 acres', '50 acres', '100 acres'];
  const yearOptions = ['', ...Array.from({ length: 2024 - 1900 + 1 }, (_, i) => (1900 + i).toString())];

  // Add debounced values for filters
  const debouncedSearch = useDebounce(search, 500);
  const debouncedMinPrice = useDebounce(minPrice, 500);
  const debouncedMaxPrice = useDebounce(maxPrice, 500);
  const debouncedBedrooms = useDebounce(bedrooms, 500);
  const debouncedBathrooms = useDebounce(bathrooms, 500);
  const debouncedSelectedHomeTypes = useDebounce(selectedHomeTypes, 500);
  const debouncedSqftMin = useDebounce(sqftMin, 500);
  const debouncedSqftMax = useDebounce(sqftMax, 500);
  const debouncedLotMin = useDebounce(lotMin, 500);
  const debouncedLotMax = useDebounce(lotMax, 500);
  const debouncedYearMin = useDebounce(yearMin, 500);
  const debouncedYearMax = useDebounce(yearMax, 500);

  // Define price options for sale and for rent
  const priceOptionsForSale = [
    '', '0', '50000', '100000', '150000', '200000', '250000', '300000', '350000', '400000', '450000', '500000',
    '550000', '600000', '650000', '700000', '750000', '800000', '850000', '900000', '950000',
    '1000000', '1250000', '1500000', '1750000', '2000000', '2500000', '2750000', '3000000', '3250000', '3500000',
    '3750000', '4000000', '4250000', '4500000', '4750000', '5000000', '5500000', '6000000', '6500000', '7000000',
    '7500000', '8000000', '8500000', '9000000', '9500000', '10000000', '11000000', '12000000', '13000000', '14000000'
  ];
  const priceLabelsForSale = [
    'No Min', '$0', '$50,000', '$100,000', '$150,000', '$200,000', '$250,000', '$300,000', '$350,000', '$400,000', '$450,000', '$500,000',
    '$550,000', '$600,000', '$650,000', '$700,000', '$750,000', '$800,000', '$850,000', '$900,000', '$950,000',
    '$1M', '$1.25M', '$1.5M', '$1.75M', '$2M', '$2.5M', '$2.75M', '$3M', '$3.25M', '$3.5M',
    '$3.75M', '$4M', '$4.25M', '$4.5M', '$4.75M', '$5M', '$5.5M', '$6M', '$6.5M', '$7M',
    '$7.5M', '$8M', '$8.5M', '$9M', '$9.5M', '$10M', '$11M', '$12M', '$13M', '$14M'
  ];
  const maxPriceOptionsForSale = [
    '', '50000', '100000', '150000', '200000', '250000', '300000', '350000', '400000', '450000', '500000',
    '550000', '600000', '650000', '700000', '750000', '800000', '850000', '900000', '950000',
    '1000000', '1250000', '1500000', '1750000', '2000000', '2500000', '2750000', '3000000', '3250000', '3500000',
    '3750000', '4000000', '4250000', '4500000', '4750000', '5000000', '5500000', '6000000', '6500000', '7000000',
    '7500000', '8000000', '8500000', '9000000', '9500000', '10000000', '11000000', '12000000', '13000000', '14000000'
  ];
  const maxPriceLabelsForSale = [
    'Any Price', '$50,000', '$100,000', '$150,000', '$200,000', '$250,000', '$300,000', '$350,000', '$400,000', '$450,000', '$500,000',
    '$550,000', '$600,000', '$650,000', '$700,000', '$750,000', '$800,000', '$850,000', '$900,000', '$950,000',
    '$1M', '$1.25M', '$1.5M', '$1.75M', '$2M', '$2.5M', '$2.75M', '$3M', '$3.25M', '$3.5M',
    '$3.75M', '$4M', '$4.25M', '$4.5M', '$4.75M', '$5M', '$5.5M', '$6M', '$6.5M', '$7M',
    '$7.5M', '$8M', '$8.5M', '$9M', '$9.5M', '$10M', '$11M', '$12M', '$13M', '$14M'
  ];

  const priceOptionsForRent = [
    '', '0', '200', '400', '600', '800', '1000', '1200', '1400', '1600', '1800', '2000', '2200', '2400', '2600', '2800', '3000', '3500', '4000', '4500', '5000', '5500', '6000', '7000', '8000', '9000', '10000'
  ];
  const priceLabelsForRent = [
    'No Min', '$0', '$200', '$400', '$600', '$800', '$1,000', '$1,200', '$1,400', '$1,600', '$1,800', '$2,000', '$2,200', '$2,400', '$2,600', '$2,800', '$3,000', '$3,500', '$4,000', '$4,500', '$5,000', '$5,500', '$6,000', '$7,000', '$8,000', '$9,000', '$10,000'
  ];
  const maxPriceOptionsForRent = [
    '', '200', '400', '600', '800', '1000', '1200', '1400', '1600', '1800', '2000', '2200', '2400', '2600', '2800', '3000', '3500', '4000', '4500', '5000', '5500', '6000', '7000', '8000', '9000', '10000'
  ];
  const maxPriceLabelsForRent = [
    'Any Price', '$200', '$400', '$600', '$800', '$1,000', '$1,200', '$1,400', '$1,600', '$1,800', '$2,000', '$2,200', '$2,400', '$2,600', '$2,800', '$3,000', '$3,500', '$4,000', '$4,500', '$5,000', '$5,500', '$6,000', '$7,000', '$8,000', '$9,000', '$10,000'
  ];

  const priceOptions = listingTypeValue === 'for_rent' ? priceOptionsForRent : priceOptionsForSale;
  const priceLabels = listingTypeValue === 'for_rent' ? priceLabelsForRent : priceLabelsForSale;
  const maxPriceOptions = listingTypeValue === 'for_rent' ? maxPriceOptionsForRent : maxPriceOptionsForSale;
  const maxPriceLabels = listingTypeValue === 'for_rent' ? maxPriceLabelsForRent : maxPriceLabelsForSale;

  // Memoize the fetchProperties function
  const debouncedFetchProperties = useCallback(
    async (
      source: 'db' | 'market',
      pageArg?: number,
      pageSizeArg?: number,
      sortCol?: string,
      sortDir?: 'asc' | 'desc',
    ) => {
      if (!locationId) return;
      try {
        setLoading(true);
        setError(null);
        let data;
        if (source === 'db') {
          // Build query string with all filters
          let url = `/api/zillow/properties?page=${pageArg || 1}` +
            `&page_size=${pageSizeArg || pageSize}` +
            `&sort_column=${sortCol || sortColumn}` +
            `&sort_direction=${sortDir || sortDirection}` +
            `${locationId ? `&locationId=${encodeURIComponent(locationId)}` : ''}` +
            `&listing_type=${listingTypeValue}` +
            (selectedHomeTypes.length > 0 ? `&home_types=${selectedHomeTypes.join(',')}` : '') +
            (minPrice ? `&min_price=${minPrice}` : '') +
            (maxPrice ? `&max_price=${maxPrice}` : '') +
            (bedrooms ? `&bedrooms=${bedrooms}` : '') +
            (bathrooms ? `&bathrooms=${bathrooms}` : '') +
            (sqftMin ? `&sqft_min=${sqftMin}` : '') +
            (sqftMax ? `&sqft_max=${sqftMax}` : '') +
            (lotMin ? `&lot_min=${lotMin}` : '') +
            (lotMax ? `&lot_max=${lotMax}` : '') +
            (yearMin ? `&year_min=${yearMin}` : '') +
            (yearMax ? `&year_max=${yearMax}` : '') +
            (search ? `&search=${encodeURIComponent(search)}` : '');
          const response = await api.get(url);
          data = response.data;
          if (data.error) {
            setError(data.error);
            setProperties([]);
            setFilteredProperties([]);
            setTotalResults(0);
            setPage(1);
            setBackgroundFetching(false);
            return;
          }
          setProperties(Array.isArray(data.properties) ? data.properties : []);
          setFilteredProperties(Array.isArray(data.properties) ? data.properties : []);
          setTotalResults(data.total_results || 0);
          setPage(data.page || 1);
          setBackgroundFetching(!!data.background_fetching);
        } else {
          const url = buildSearchUrl();
          const response = await api.get(`/api/zillow/search?url=${encodeURIComponent(url)}&page=${pageArg || 1}&page_size=${pageSizeArg || pageSize}${locationId ? `&locationId=${encodeURIComponent(locationId)}` : ''}`);
          const result = response.data;
          if (result.success) {
            setProperties(result.properties);
            setFilteredProperties(result.properties);
            setTotalResults(result.total_results);
            if (result.total_pages) setPage(result.page || 1);
          } else {
            setError(result.error || 'Failed to search on Zillow');
            setProperties([]);
            setFilteredProperties([]);
            setTotalResults(0);
            setPage(1);
          }
        }
      } catch (err) {
        setError('Failed to fetch properties');
        console.error('Error fetching properties:', err);
      } finally {
        setLoading(false);
      }
    },
    [locationId, pageSize, sortColumn, sortDirection, listingTypeValue, minPrice, maxPrice, bedrooms, bathrooms, sqftMin, sqftMax, lotMin, lotMax, yearMin, yearMax, search, selectedHomeTypes]
  );

  // On mount, fetch from DB only once
  useEffect(() => {
    if (!locationId) return; // Do not fetch if locationId is not set
    setDataSource('db');
    setHasSearched(false);
    fetchProperties('db', 1, pageSize);
    // eslint-disable-next-line
  }, [locationId]);

  useEffect(() => {
    // Try to get from query string
    const params = new URLSearchParams(window.location.search);
    let locId = params.get("locationId");
    // If not found, try from pathname (e.g. /locationId=xxxx)
    if (!locId) {
      const match = window.location.pathname.match(/locationId=([^\/]+)/);
      if (match) locId = match[1];
    }
    setLocationId(locId);
  }, []);

  // When properties change, update filteredProperties
  useEffect(() => {
    setFilteredProperties(
      properties.filter((prop) => {
        const searchLower = search.toLowerCase();
        return (
          (prop.street_address && prop.street_address.toLowerCase().includes(searchLower)) ||
          (prop.city && prop.city.toLowerCase().includes(searchLower)) ||
          (prop.state && prop.state.toLowerCase().includes(searchLower)) ||
          (((prop.zip_code || prop.zipcode)?.toLowerCase() ?? '').includes(searchLower))
        );
      })
    );
  }, [properties, search]);

  // On search input change, update search and filteredProperties
  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setFilteredProperties(
      properties.filter((prop) => {
        const searchLower = e.target.value.toLowerCase();
        return (
          (prop.street_address && prop.street_address.toLowerCase().includes(searchLower)) ||
          (prop.city && prop.city.toLowerCase().includes(searchLower)) ||
          (prop.state && prop.state.toLowerCase().includes(searchLower)) ||
          (((prop.zip_code || prop.zipcode)?.toLowerCase() ?? '').includes(searchLower))
        );
      })
    );
  };

  // When fetching from market, update both properties and filteredProperties
  const fetchProperties = async (
    source: 'db' | 'market',
    pageArg?: number,
    pageSizeArg?: number,
    sortCol?: string,
    sortDir?: 'asc' | 'desc',
  ) => {
    if (!locationId) {
      // Do not fetch if locationId is not set
      return;
    }
    try {
      setLoading(true);
      setError(null);
      let data;
      if (source === 'db') {
        // Build query string with all filters
        let url = `/api/zillow/properties?page=${pageArg || 1}` +
          `&page_size=${pageSizeArg || pageSize}` +
          `&sort_column=${sortCol || sortColumn}` +
          `&sort_direction=${sortDir || sortDirection}` +
          `${locationId ? `&locationId=${encodeURIComponent(locationId)}` : ''}` +
          `&listing_type=${listingTypeValue}` +
          (selectedHomeTypes.length > 0 ? `&home_types=${selectedHomeTypes.join(',')}` : '') +
          (minPrice ? `&min_price=${minPrice}` : '') +
          (maxPrice ? `&max_price=${maxPrice}` : '') +
          (bedrooms ? `&bedrooms=${bedrooms}` : '') +
          (bathrooms ? `&bathrooms=${bathrooms}` : '') +
          (sqftMin ? `&sqft_min=${sqftMin}` : '') +
          (sqftMax ? `&sqft_max=${sqftMax}` : '') +
          (lotMin ? `&lot_min=${lotMin}` : '') +
          (lotMax ? `&lot_max=${lotMax}` : '') +
          (yearMin ? `&year_min=${yearMin}` : '') +
          (yearMax ? `&year_max=${yearMax}` : '') +
          (search ? `&search=${encodeURIComponent(search)}` : '');
        const response = await api.get(url);
        data = response.data;
        if (data.error) {
          setError(data.error);
          setProperties([]);
          setFilteredProperties([]);
          setTotalResults(0);
          setPage(1);
          setBackgroundFetching(false);
          return;
        }
        setProperties(Array.isArray(data.properties) ? data.properties : []);
        setFilteredProperties(Array.isArray(data.properties) ? data.properties : []);
        setTotalResults(data.total_results || 0);
        setPage(data.page || 1);
        setBackgroundFetching(!!data.background_fetching);
      } else {
        // Market search (local sort fallback)
        const url = buildSearchUrl();
        const response = await api.get(`/api/zillow/search?url=${encodeURIComponent(url)}&page=${pageArg || 1}&page_size=${pageSizeArg || pageSize}${locationId ? `&locationId=${encodeURIComponent(locationId)}` : ''}`);
        const result = response.data;
        if (result.success) {
          setProperties(result.properties);
          setFilteredProperties(result.properties);
          setTotalResults(result.total_results);
          if (result.total_pages) setPage(result.page || 1);
        } else {
          setError(result.error || 'Failed to search on Zillow');
          setProperties([]);
          setFilteredProperties([]);
          setTotalResults(0);
          setPage(1);
        }
      }
    } catch (err) {
      setError('Failed to fetch properties');
      console.error('Error fetching properties:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (_: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
    if (!loading) {
      if (dataSource === 'db' && !hasSearched) fetchProperties('db', value, pageSize);
      if (dataSource === 'market' && hasSearched) fetchProperties('market', value, pageSize);
    }
  };
  const handleSelectProperty = (propertyId: string) => {
    setSelectedProperties(prev => {
      const newSelected = new Set(prev);
      if (newSelected.has(propertyId)) {
        newSelected.delete(propertyId);
      } else {
        newSelected.add(propertyId);
      }
      return newSelected;
    });
  };

  const handleSelectAll = () => {
    if (selectedProperties.size === properties.length) {
      setSelectedProperties(new Set());
    } else {
      const allIds = properties.map(prop => String(prop.id || ''));
      setSelectedProperties(new Set(allIds));
    }
  };

  const handleSendToCyclSales = async () => {
    setLoadingSendToCS(true);
    try {
      const selectedIds = Array.from(selectedProperties).map(id => Number(id));
      const result = await zillowService.sendToCyclSales(selectedIds, locationId || undefined);
      if (result.success) {
        // Fade out sent properties
        setFadingProperties(new Set(selectedProperties));
        setTimeout(() => {
          setProperties(prev => prev.filter(prop => !selectedProperties.has(String(prop.id || ''))));
          setFilteredProperties(prev => prev.filter(prop => !selectedProperties.has(String(prop.id || ''))));
          setSelectedProperties(new Set());
          setFadingProperties(new Set());
        }, 500); // 500ms fade duration
        setShowSendToCyclSalesPopup(false);
      } else {
        setError(result.error || 'Failed to send properties to CyclSales');
      }
    } catch (err) {
      setError('Failed to send properties to CyclSales');
    } finally {
      setLoadingSendToCS(false);
    }
  };

  const handlePriceMenuOpen = (event: React.MouseEvent<HTMLElement>) => setPriceAnchorEl(event.currentTarget);
  const handlePriceMenuClose = () => setPriceAnchorEl(null);
  const handleMinPriceChange = (event: SelectChangeEvent) => {
    setMinPrice(event.target.value);
    fetchProperties(dataSource, 1, pageSize);
  };
  const handleMaxPriceChange = (event: SelectChangeEvent) => {
    setMaxPrice(event.target.value);
    fetchProperties(dataSource, 1, pageSize);
  };
  const handleApplyPrice = () => {
    // TODO: Use minPrice and maxPrice in your search/filter logic
    handlePriceMenuClose();
  };

  const handleListingTypeMenuOpen = (event: React.MouseEvent<HTMLElement>) => setListingTypeAnchorEl(event.currentTarget);
  const handleListingTypeMenuClose = () => setListingTypeAnchorEl(null);
  const handleListingTypeRadioChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setListingTypeValue(event.target.value as 'for_sale' | 'for_rent' | 'sold');
    fetchProperties(dataSource, 1, pageSize);
  };
  const handleApplyListingType = () => {
    // TODO: Use listingTypeValue in your search/filter logic
    handleListingTypeMenuClose();
  };

  const handleBedsBathsMenuOpen = (event: React.MouseEvent<HTMLElement>) => setBedsBathsAnchorEl(event.currentTarget);
  const handleBedsBathsMenuClose = () => setBedsBathsAnchorEl(null);
  const handleBedroomsChange = (val: string) => {
    setBedrooms(val);
    fetchProperties(dataSource, 1, pageSize);
  };
  const handleBathroomsChange = (val: string) => {
    setBathrooms(val);
    fetchProperties(dataSource, 1, pageSize);
  };
  const handleExactMatchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setExactMatch(event.target.checked);
    fetchProperties(dataSource, 1, pageSize);
  };
  const handleApplyBedsBaths = () => {
    // TODO: Use bedrooms, bathrooms, exactMatch in your search/filter logic
    handleBedsBathsMenuClose();
  };

  const handleHomeTypeMenuOpen = (event: React.MouseEvent<HTMLElement>) => setHomeTypeAnchorEl(event.currentTarget);
  const handleHomeTypeMenuClose = () => setHomeTypeAnchorEl(null);
  const handleHomeTypeChange = (value: string) => {
    setSelectedHomeTypes(prev => {
      const updated = prev.includes(value) ? prev.filter(v => v !== value) : [...prev, value];
      setTimeout(() => fetchProperties(dataSource, 1, pageSize), 0);
      return updated;
    });
  };
  const handleDeselectAllHomeTypes = () => {
    if (selectedHomeTypes.length === homeTypeOptions.length) {
      setSelectedHomeTypes([]);
    } else {
      setSelectedHomeTypes(homeTypeOptions.map(o => o.value));
    }
    fetchProperties(dataSource, 1, pageSize);
  };
  const handleApplyHomeType = () => {
    // TODO: Use selectedHomeTypes in your search/filter logic
    handleHomeTypeMenuClose();
  };

  const handleMoreMenuOpen = (event: React.MouseEvent<HTMLElement>) => setMoreAnchorEl(event.currentTarget);
  const handleMoreMenuClose = () => setMoreAnchorEl(null);
  const handleResetAllFilters = () => {
    setSqftMin(''); setSqftMax(''); setLotMin(''); setLotMax(''); setYearMin(''); setYearMax('');
    setHasBasement(false); setTour3D(false); setInstantTour(false);
    setAllowsLargeDogs(false); setAllowsSmallDogs(false); setAllowsCats(false); setNoPets(false);
    setMustHaveAC(false); setMustHavePool(false); setWaterfront(false); setOnSiteParking(false);
    setInUnitLaundry(false); setAcceptsZillowApps(false); setIncomeRestricted(false);
    setHardwoodFloors(false); setDisabledAccess(false); setUtilitiesIncluded(false);
    setShortTermLease(false); setFurnished(false); setOutdoorSpace(false); setControlledAccess(false);
    setHighSpeedInternet(false); setElevator(false); setApartmentCommunity(false);
    setViewCity(false); setViewMountain(false); setViewPark(false); setViewWater(false);
    setCommute(''); setDaysOnZillow(''); setKeywords(''); setFiftyFivePlus('include');
  };
  const handleApplyMore = () => {
    // TODO: Use all filter values in your search/filter logic
    handleMoreMenuClose();
  };

  // Sorting handler
  const handleSort = (column: string) => {
    let newDirection: 'asc' | 'desc' = 'asc';
    if (sortColumn === column) {
      newDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    }
    setSortColumn(column);
    setSortDirection(newDirection);
    if (dataSource === 'db' && !hasSearched) {
      if (!locationId) return; // Do not fetch if locationId is not set
      fetchProperties('db', 1, pageSize, column, newDirection);
    } else {
      // For market data, just update state and let local sort apply
      setSortColumn(column);
      setSortDirection(newDirection);
    }
  };

  // Sort filteredProperties before rendering
  const sortedProperties = (dataSource === 'market' && hasSearched)
    ? [...filteredProperties].sort((a, b) => {
      if (!sortColumn) return 0;
      let aValue: any = a[sortColumn as keyof typeof a];
      let bValue: any = b[sortColumn as keyof typeof b];
      // For address, sort by street_address
      if (sortColumn === 'address') {
        aValue = a.street_address ?? '';
        bValue = b.street_address ?? '';
      }
      // For type, sort by home_type
      if (sortColumn === 'type') {
        aValue = a.home_type ?? '';
        bValue = b.home_type ?? '';
      }
      // For status, sort by home_status
      if (sortColumn === 'status') {
        aValue = a.home_status ?? '';
        bValue = b.home_status ?? '';
      }
      // For sent_to_cyclsales_count, ensure number
      if (sortColumn === 'sent_to_cyclsales_count') {
        aValue = a.sent_to_cyclsales_count ?? 0;
        bValue = b.sent_to_cyclsales_count ?? 0;
      }
      // For numeric columns
      if ([
        'price', 'bedrooms', 'bathrooms', 'living_area', 'sent_to_cyclsales_count'
      ].includes(sortColumn)) {
        aValue = Number(aValue ?? 0);
        bValue = Number(bValue ?? 0);
      }
      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    })
    : filteredProperties;

  // Function to build the current Zillow search URL with all filters
  const buildSearchUrl = () => {
    const baseUrl = `https://www.zillow.com/${search ? encodeURIComponent(search) + '/' : ''}${listingTypeValue === 'for_rent' ? 'rentals/' : listingTypeValue === 'sold' ? 'sold/' : ''}`;
    const searchQueryState: any = {
      pagination: {
        currentPage: page
      },
      mapBounds: {
        west: -87.7266194819336, // Example: Chicago
        east: -87.60645651806641,
        south: 41.70463730273328,
        north: 41.79492639691581
      },
      isMapVisible: true,
      isListVisible: true,
      filterState: {
        sort: { value: 'globalrelevanceex' },
        // Set listing type filters
        fr: { value: listingTypeValue === 'for_rent' },
        fsba: { value: listingTypeValue === 'for_sale' },
        fsbo: { value: false },
        nc: { value: false },
        cmsn: { value: false },
        auc: { value: false },
        fore: { value: false }
      },
      usersSearchTerm: search || '',
    };

    // Price
    if (minPrice) searchQueryState.filterState.price = { min: parseInt(minPrice) };
    if (maxPrice) searchQueryState.filterState.price = { ...searchQueryState.filterState.price, max: parseInt(maxPrice) };
    // Monthly payment (mp)
    // Add if you have UI for it
    // Beds & Baths
    if (bedrooms) searchQueryState.filterState.beds = { min: parseInt(bedrooms) };
    if (bathrooms) searchQueryState.filterState.baths = { min: parseFloat(bathrooms) };
    // Home Type
    if (selectedHomeTypes.length > 0) {
      // Map to Zillow's home type keys
      if (selectedHomeTypes.includes('SINGLE_FAMILY')) searchQueryState.filterState.isSingleFamily = { value: true };
      if (selectedHomeTypes.includes('TOWNHOUSE')) searchQueryState.filterState.isTownhouse = { value: true };
      if (selectedHomeTypes.includes('MULTI_FAMILY')) searchQueryState.filterState.isMultiFamily = { value: true };
      if (selectedHomeTypes.includes('CONDO')) searchQueryState.filterState.isCondo = { value: true };
      if (selectedHomeTypes.includes('LOT')) searchQueryState.filterState.isLotLand = { value: true };
      if (selectedHomeTypes.includes('APARTMENT')) searchQueryState.filterState.isApartment = { value: true };
      if (selectedHomeTypes.includes('MANUFACTURED')) searchQueryState.filterState.isManufactured = { value: true };
    }
    // Square Footage
    if (sqftMin) searchQueryState.filterState.sqft = { ...searchQueryState.filterState.sqft, min: parseInt(sqftMin) };
    if (sqftMax) searchQueryState.filterState.sqft = { ...searchQueryState.filterState.sqft, max: parseInt(sqftMax) };
    // Lot Size
    if (lotMin) searchQueryState.filterState.lot = { ...searchQueryState.filterState.lot, min: parseInt(lotMin) };
    if (lotMax) searchQueryState.filterState.lot = { ...searchQueryState.filterState.lot, max: parseInt(lotMax) };
    // Year Built
    if (yearMin) searchQueryState.filterState.built = { ...searchQueryState.filterState.built, min: parseInt(yearMin) };
    if (yearMax) searchQueryState.filterState.built = { ...searchQueryState.filterState.built, max: parseInt(yearMax) };
    // Features
    if (tour3D) searchQueryState.filterState['3d'] = { value: true };
    if (mustHaveAC) searchQueryState.filterState.ac = { value: true };
    if (hasBasement) searchQueryState.filterState.basf = { value: true };
    if (onSiteParking) searchQueryState.filterState.gar = { value: true };
    if (mustHavePool) searchQueryState.filterState.pool = { value: true };
    if (waterfront) searchQueryState.filterState.water = { value: true };
    // Days on Zillow
    if (daysOnZillow) searchQueryState.filterState.doz = { value: daysOnZillow + 'm' };
    // Add more filters as needed from UI state

    const params = new URLSearchParams({
      searchQueryState: JSON.stringify(searchQueryState),
    });
    return `${baseUrl}?${params.toString()}`;
  };

  // Update useEffect to use debounced values
  useEffect(() => {
    if (!locationId) return;
    if (dataSource === 'db' && !hasSearched) {
      debouncedFetchProperties('db', 1, pageSize, sortColumn, sortDirection);
    }
  }, [
    debouncedSearch,
    debouncedMinPrice,
    debouncedMaxPrice,
    debouncedBedrooms,
    debouncedBathrooms,
    debouncedSelectedHomeTypes,
    debouncedSqftMin,
    debouncedSqftMax,
    debouncedLotMin,
    debouncedLotMax,
    debouncedYearMin,
    debouncedYearMax,
    hasBasement,
    tour3D,
    instantTour,
    allowsLargeDogs,
    allowsSmallDogs,
    allowsCats,
    noPets,
    mustHaveAC,
    mustHavePool,
    waterfront,
    onSiteParking,
    inUnitLaundry,
    acceptsZillowApps,
    incomeRestricted,
    hardwoodFloors,
    disabledAccess,
    utilitiesIncluded,
    shortTermLease,
    furnished,
    outdoorSpace,
    controlledAccess,
    highSpeedInternet,
    elevator,
    apartmentCommunity,
    viewCity,
    viewMountain,
    viewPark,
    viewWater,
    commute,
    daysOnZillow,
    keywords,
    fiftyFivePlus,
    debouncedFetchProperties,
    dataSource,
    hasSearched,
    pageSize,
    sortColumn,
    sortDirection
  ]);

  // Helper to collect current filters for summary
  const getCurrentFilters = () => ({
    Listing_Type: listingTypeValue === 'for_sale' ? 'For Sale' : listingTypeValue === 'for_rent' ? 'For Rent' : 'Sold',
    Min_Price: minPrice,
    Max_Price: maxPrice,
    Bedrooms: bedrooms,
    Bathrooms: bathrooms,
    Sqft_Min: sqftMin,
    Sqft_Max: sqftMax,
    Lot_Min: lotMin,
    Lot_Max: lotMax,
    Year_Min: yearMin,
    Year_Max: yearMax,
    Home_Types: selectedHomeTypes,
    Has_Basement: hasBasement,
    Must_Have_AC: mustHaveAC,
    Must_Have_Pool: mustHavePool,
    Waterfront: waterfront,
    On_Site_Parking: onSiteParking,
    In_Unit_Laundry: inUnitLaundry,
    Accepts_Zillow_Apps: acceptsZillowApps,
    Income_Restricted: incomeRestricted,
    Hardwood_Floors: hardwoodFloors,
    Disabled_Access: disabledAccess,
    Utilities_Included: utilitiesIncluded,
    Short_Term_Lease: shortTermLease,
    Furnished: furnished,
    Outdoor_Space: outdoorSpace,
    Controlled_Access: controlledAccess,
    High_Speed_Internet: highSpeedInternet,
    Elevator: elevator,
    Apartment_Community: apartmentCommunity,
    View_City: viewCity,
    View_Mountain: viewMountain,
    View_Park: viewPark,
    View_Water: viewWater,
    Days_On_Zillow: daysOnZillow,
    Keywords: keywords,
    Fifty_Five_Plus: fiftyFivePlus,
  });

  // Update handleSearchOnZillow to always pass address and location
  const handleSearchOnZillow = async (pageOverride?: number, pageSizeOverride?: number) => {
    if (!locationId) {
      setError('No locationId provided in the URL. Please access this app from the authorized menu.');
      return;
    }
    setDataSource('market');
    setHasSearched(true);
    if (pageOverride) setPage(pageOverride);
    if (pageSizeOverride) setPageSize(pageSizeOverride);
    setLoading(true);
    setError(null);

    // Map listingTypeValue to home_status for backend
    const homeStatusMap: Record<string, string> = {
      for_sale: 'FOR_SALE',
      for_rent: 'FOR_RENT',
      sold: 'SOLD',
    };
    const homeStatus = homeStatusMap[listingTypeValue] || 'FOR_SALE';

    // Always use 'by_agent' for the API call
    let url = `/api/zillow/search?search_on_market=1` +
      `&locationId=${encodeURIComponent(locationId)}` +
      `&page=${pageOverride || 1}` +
      `&page_size=${pageSizeOverride || pageSize}` +
      `&listing_type=by_agent` +
      `&home_status=${homeStatus}` +
      (selectedHomeTypes.length > 0 ? `&home_types=${selectedHomeTypes.join(',')}` : '') +
      (minPrice ? `&min_price=${minPrice}` : '') +
      (maxPrice ? `&max_price=${maxPrice}` : '') +
      (bedrooms ? `&bedrooms=${bedrooms}` : '') +
      (bathrooms ? `&bathrooms=${bathrooms}` : '') +
      (sqftMin ? `&sqft_min=${sqftMin}` : '') +
      (sqftMax ? `&sqft_max=${sqftMax}` : '') +
      (lotMin ? `&lot_min=${lotMin}` : '') +
      (lotMax ? `&lot_max=${lotMax}` : '') +
      (yearMin ? `&year_min=${yearMin}` : '') +
      (yearMax ? `&year_max=${yearMax}` : '') +
      `&address=${encodeURIComponent(search || '')}` +
      `&location=${encodeURIComponent(search || locationId)}`;

    try {
      const response = await api.get(url);
      const result = response.data;
      if (result.success || result.properties) {
        setProperties(result.properties);
        setFilteredProperties(result.properties);
        setTotalResults(result.total_results);
        if (result.total_pages) setPage(result.page || 1);
      } else {
        setError(result.error || 'Failed to search on Zillow');
        setProperties([]);
        setFilteredProperties([]);
        setTotalResults(0);
        setPage(1);
      }
    } catch (err) {
      setError('Failed to fetch properties');
      console.error('Error fetching properties:', err);
    } finally {
      setLoading(false);
    }
  };

  // PageSizeSelector with skeleton
  const PageSizeSelector = ({ totalResults, pageSize, page, onPageSizeChange, loading }: {
    totalResults: number,
    pageSize: number,
    page: number,
    onPageSizeChange: (newSize: number) => void,
    loading: boolean
  }) => {
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const startRecord = ((page - 1) * pageSize) + 1;
    const endRecord = Math.min(page * pageSize, totalResults);

    const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
      setAnchorEl(event.currentTarget);
    };

    const handleClose = () => {
      setAnchorEl(null);
    };

    const pageSizes = [10, 20, 50, 80, 100, 200];

    if (loading) {
      return <Skeleton variant="text" width={80} height={32} />;
    }

    return (
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Box
          onClick={handleClick}
          sx={{
            cursor: 'pointer',
            color: '#2563eb',
            '&:hover': { textDecoration: 'underline' },
            fontSize: '0.875rem',
            fontWeight: 500,
          }}
        >
          {`${startRecord}-${endRecord} / ${totalResults}`}
        </Box>
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
        >
          {pageSizes.map((size) => (
            <MenuItem
              key={size}
              onClick={() => {
                onPageSizeChange(size);
                handleClose();
              }}
              selected={pageSize === size}
            >
              {size} records
            </MenuItem>
          ))}
        </Menu>
      </Box>
    );
  };

  // Improved Skeleton for table rows
  const TableSkeleton = ({ rows = 10 }: { rows?: number }) => (
    <TableBody>
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <TableRow key={rowIdx}>
          {/* Checkbox */}
          <TableCell padding="checkbox">
            <Skeleton variant="circular" width={24} height={24} />
          </TableCell>
          {/* Image */}
          <TableCell>
            <Skeleton variant="rectangular" width={100} height={75} />
          </TableCell>
          {/* Address */}
          <TableCell>
            <Skeleton variant="text" width={120} height={24} />
            <Skeleton variant="text" width={80} height={18} />
          </TableCell>
          {/* Price */}
          <TableCell>
            <Skeleton variant="rounded" width={60} height={32} />
          </TableCell>
          {/* Beds */}
          <TableCell>
            <Skeleton variant="rounded" width={40} height={32} />
          </TableCell>
          {/* Baths */}
          <TableCell>
            <Skeleton variant="rounded" width={40} height={32} />
          </TableCell>
          {/* Sq Ft */}
          <TableCell>
            <Skeleton variant="text" width={50} height={24} />
          </TableCell>
          {/* Type */}
          <TableCell>
            <Skeleton variant="text" width={70} height={24} />
          </TableCell>
          {/* Status */}
          <TableCell>
            <Skeleton variant="rounded" width={70} height={32} />
          </TableCell>
          {/* Sent to CS */}
          <TableCell>
            <Skeleton variant="rounded" width={60} height={24} />
          </TableCell>
          {/* Actions */}
          <TableCell>
            <Skeleton variant="rectangular" width={90} height={32} />
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  );

  const handleCheckboxChange = (setter: React.Dispatch<React.SetStateAction<boolean>>) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setter(e.target.checked);
    fetchProperties(dataSource, 1, pageSize);
  };

  const handleSqftMinChange = (e: SelectChangeEvent) => {
    setSqftMin(e.target.value);
    fetchProperties(dataSource, 1, pageSize);
  };
  const handleSqftMaxChange = (e: SelectChangeEvent) => {
    setSqftMax(e.target.value);
    fetchProperties(dataSource, 1, pageSize);
  };
  const handleLotMinChange = (e: SelectChangeEvent) => {
    setLotMin(e.target.value);
    fetchProperties(dataSource, 1, pageSize);
  };
  const handleLotMaxChange = (e: SelectChangeEvent) => {
    setLotMax(e.target.value);
    fetchProperties(dataSource, 1, pageSize);
  };
  const handleYearMinChange = (e: SelectChangeEvent) => {
    setYearMin(e.target.value);
    fetchProperties(dataSource, 1, pageSize);
  };
  const handleYearMaxChange = (e: SelectChangeEvent) => {
    setYearMax(e.target.value);
    fetchProperties(dataSource, 1, pageSize);
  };

  useEffect(() => {
    if (backgroundFetching) {
      const timer = setTimeout(() => setBackgroundFetching(false), 8000); // 8 seconds
      return () => clearTimeout(timer);
    }
  }, [backgroundFetching]);

  if (!locationId) {
    return (
      <ThemeProvider theme={theme}>
        <Box sx={{ p: 4 }}>
          <Alert severity="error">
            No locationId provided in the URL. Please access this app from the authorized menu.
          </Alert>
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', py: 6, width: '100vw' }}>
        <Box sx={{ width: '100%', px: { xs: 1, sm: 3, md: 6, lg: 10 }, boxSizing: 'border-box' }}>
          {/* Search UI */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4, width: '100%' }}>
            <OutlinedInput
              placeholder="Address, neighborhood, city, ZIP"
              sx={{
                flex: 1,
                borderRadius: '5px',
                bgcolor: '#fff',
                fontSize: 14,
                height: 36,
                minHeight: 36,
                '.MuiOutlinedInput-input': {
                  py: 0.5,
                  fontSize: 14,
                  height: 36,
                  minHeight: 36,
                },
              }}
              value={search}
              onChange={handleSearchInputChange}
              endAdornment={
                <InputAdornment position="end">
                  <IconButton edge="end" size="small" sx={{ height: 28, width: 28 }}>
                    <SearchIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              }
            />
            <Button
              variant="outlined"
              endIcon={<ArrowDropDownIcon />}
              sx={{
                height: 36,
                borderRadius: '5px',
                fontWeight: 500,
                fontSize: 14,
                minWidth: 120,
                px: 2,
                textTransform: 'none',
                bgcolor: '#fff',
                color: '#222',
                borderColor: '#d1d5db',
                boxShadow: 'none',
                '&:hover': {
                  bgcolor: '#f5f6fa',
                  borderColor: '#2563eb',
                  color: '#2563eb',
                },
                '&.Mui-focused, &.Mui-active': {
                  borderColor: '#2563eb',
                  color: '#2563eb',
                },
              }}
              onClick={handleListingTypeMenuOpen}
            >
              {listingTypeValue === 'for_sale' ? 'For Sale' : listingTypeValue === 'for_rent' ? 'For Rent' : 'Sold'}
            </Button>
            <Menu
              anchorEl={listingTypeAnchorEl}
              open={Boolean(listingTypeAnchorEl)}
              onClose={handleListingTypeMenuClose}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
              transformOrigin={{ vertical: 'top', horizontal: 'left' }}
              PaperProps={{
                sx: {
                  borderRadius: 3,
                  minWidth: 340,
                  p: 0,
                  boxShadow: 6,
                  mt: 1,
                }
              }}
            >
              <Box sx={{ px: 3, py: 3 }}>
                <RadioGroup value={listingTypeValue} onChange={handleListingTypeRadioChange}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Radio value="for_sale" sx={{ color: '#b0b0b0', '&.Mui-checked': { color: '#2563eb' } }} />
                    <Typography sx={{ fontWeight: 500, color: '#222', fontSize: 18 }}>For Sale</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Radio value="for_rent" sx={{ color: '#b0b0b0', '&.Mui-checked': { color: '#2563eb' } }} />
                    <Typography sx={{ fontWeight: 500, color: listingTypeValue === 'for_rent' ? '#2563eb' : '#222', fontSize: 18 }}>For Rent</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Radio value="sold" sx={{ color: '#b0b0b0', '&.Mui-checked': { color: '#2563eb' } }} />
                    <Typography sx={{ fontWeight: 500, color: listingTypeValue === 'sold' ? '#2563eb' : '#222', fontSize: 18 }}>Sold</Typography>
                  </Box>
                </RadioGroup>
                <Button
                  variant="contained"
                  fullWidth
                  sx={{
                    bgcolor: '#2563eb',
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: 16,
                    borderRadius: 2,
                    height: 44,
                    mt: 2,
                    textTransform: 'none',
                    boxShadow: 'none',
                    '&:hover': { bgcolor: '#1742a0' },
                  }}
                  onClick={handleApplyListingType}
                >
                  Apply
                </Button>
              </Box>
            </Menu>
            <Button
              variant="outlined"
              endIcon={<ArrowDropDownIcon />}
              sx={{
                height: 36,
                borderRadius: '5px',
                fontWeight: 500,
                fontSize: 14,
                minWidth: 100,
                px: 2,
                textTransform: 'none',
                bgcolor: '#fff',
                color: '#222',
                borderColor: '#d1d5db',
                boxShadow: 'none',
                '&:hover': {
                  bgcolor: '#f5f6fa',
                  borderColor: '#2563eb',
                  color: '#2563eb',
                },
                '&.Mui-focused, &.Mui-active': {
                  borderColor: '#2563eb',
                  color: '#2563eb',
                },
              }}
              onClick={handlePriceMenuOpen}
            >
              Price
            </Button>
            <Menu
              anchorEl={priceAnchorEl}
              open={Boolean(priceAnchorEl)}
              onClose={handlePriceMenuClose}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
              transformOrigin={{ vertical: 'top', horizontal: 'left' }}
              PaperProps={{
                sx: {
                  borderRadius: 3,
                  minWidth: 340,
                  p: 0,
                  boxShadow: 6,
                  mt: 1,
                }
              }}
            >
              <Box sx={{ bgcolor: '#f7f8fa', px: 3, py: 2, borderTopLeftRadius: 12, borderTopRightRadius: 12 }}>
                <Typography variant="subtitle1" fontWeight={600} color="#6e6e6e">Price Range</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', px: 3, py: 2, gap: 2 }}>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle2" fontWeight={700} mb={0.5}>Minimum</Typography>
                  <FormControl fullWidth size="small">
                    <Select value={minPrice} onChange={handleMinPriceChange} displayEmpty sx={{ bgcolor: '#f7f8fa', borderRadius: 1 }}>
                      {priceOptions.map((price, idx) => (
                        <MenuItem key={price} value={price}>{priceLabels[idx]}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
                <Typography sx={{ mx: 1, color: '#6e6e6e' }}>-</Typography>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle2" fontWeight={700} mb={0.5}>Maximum</Typography>
                  <FormControl fullWidth size="small">
                    <Select value={maxPrice} onChange={handleMaxPriceChange} displayEmpty sx={{ bgcolor: '#f7f8fa', borderRadius: 1 }}>
                      {maxPriceOptions.map((price, idx) => (
                        <MenuItem key={price} value={price}>{maxPriceLabels[idx]}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
              </Box>
              <Box sx={{ px: 3, pb: 2 }}>
                <Button
                  variant="contained"
                  fullWidth
                  sx={{
                    bgcolor: '#2563eb',
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: 16,
                    borderRadius: 2,
                    height: 44,
                    mt: 1,
                    textTransform: 'none',
                    boxShadow: 'none',
                    '&:hover': { bgcolor: '#1742a0' },
                  }}
                  onClick={handleApplyPrice}
                >
                  Apply
                </Button>
              </Box>
            </Menu>
            <Button
              variant="outlined"
              endIcon={<ArrowDropDownIcon />}
              sx={{
                height: 36,
                borderRadius: '5px',
                fontWeight: 500,
                fontSize: 14,
                minWidth: 130,
                px: 2,
                textTransform: 'none',
                bgcolor: '#fff',
                color: '#222',
                borderColor: '#d1d5db',
                boxShadow: 'none',
                '&:hover': {
                  bgcolor: '#f5f6fa',
                  borderColor: '#2563eb',
                  color: '#2563eb',
                },
                '&.Mui-focused, &.Mui-active': {
                  borderColor: '#2563eb',
                  color: '#2563eb',
                },
              }}
              onClick={handleBedsBathsMenuOpen}
            >
              Beds & Baths
            </Button>
            <Menu
              anchorEl={bedsBathsAnchorEl}
              open={Boolean(bedsBathsAnchorEl)}
              onClose={handleBedsBathsMenuClose}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
              transformOrigin={{ vertical: 'top', horizontal: 'left' }}
              PaperProps={{
                sx: {
                  borderRadius: 3,
                  minWidth: 420,
                  p: 0,
                  boxShadow: 6,
                  mt: 1,
                }
              }}
            >
              <Box sx={{ bgcolor: '#f7f8fa', px: 3, py: 2, borderTopLeftRadius: 12, borderTopRightRadius: 12 }}>
                <Typography variant="subtitle1" fontWeight={600} color="#6e6e6e">Number of Bedrooms</Typography>
              </Box>
              <Box sx={{ px: 3, pt: 2, pb: 1 }}>
                <Typography variant="subtitle2" fontWeight={700} mb={1}>Bedrooms</Typography>
                <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                  {bedroomOptions.map((val, _) => (
                    <Button
                      key={val || 'any'}
                      variant={bedrooms === val ? 'contained' : 'outlined'}
                      sx={{
                        minWidth: 56,
                        bgcolor: bedrooms === val ? '#2563eb' : '#f7f8fa',
                        color: bedrooms === val ? '#fff' : '#222',
                        borderColor: bedrooms === val ? '#2563eb' : '#e0e0e0',
                        fontWeight: 600,
                        boxShadow: 'none',
                        textTransform: 'none',
                        '&:hover': { bgcolor: bedrooms === val ? '#1742a0' : '#e0e0e0' },
                      }}
                      onClick={() => handleBedroomsChange(val)}
                    >
                      {val === '' ? 'Any' : `${val}+`}
                    </Button>
                  ))}
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  <Checkbox checked={exactMatch} onChange={handleExactMatchChange} size="small" />
                  <Typography variant="body2">Use exact match</Typography>
                </Box>
              </Box>
              <Box sx={{ bgcolor: '#f7f8fa', px: 3, py: 2, mt: 2 }}>
                <Typography variant="subtitle1" fontWeight={600} color="#6e6e6e">Number of Bathrooms</Typography>
              </Box>
              <Box sx={{ px: 3, pt: 2, pb: 1 }}>
                <Typography variant="subtitle2" fontWeight={700} mb={1}>Bathrooms</Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {bathroomOptions.map((val, _) => (
                    <Button
                      key={val || 'any'}
                      variant={bathrooms === val ? 'contained' : 'outlined'}
                      sx={{
                        minWidth: 56,
                        bgcolor: bathrooms === val ? '#2563eb' : '#f7f8fa',
                        color: bathrooms === val ? '#fff' : '#222',
                        borderColor: bathrooms === val ? '#2563eb' : '#e0e0e0',
                        fontWeight: 600,
                        boxShadow: 'none',
                        textTransform: 'none',
                        '&:hover': { bgcolor: bathrooms === val ? '#1742a0' : '#e0e0e0' },
                      }}
                      onClick={() => handleBathroomsChange(val)}
                    >
                      {val === '' ? 'Any' : `${val}+`}
                    </Button>
                  ))}
                </Box>
              </Box>
              <Box sx={{ px: 3, pb: 2, pt: 1 }}>
                <Button
                  variant="contained"
                  fullWidth
                  sx={{
                    bgcolor: '#2563eb',
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: 16,
                    borderRadius: 2,
                    height: 44,
                    mt: 1,
                    textTransform: 'none',
                    boxShadow: 'none',
                    '&:hover': { bgcolor: '#1742a0' },
                  }}
                  onClick={handleApplyBedsBaths}
                >
                  Apply
                </Button>
              </Box>
            </Menu>
            <Button
              variant="outlined"
              endIcon={<ArrowDropDownIcon />}
              sx={{
                height: 36,
                borderRadius: '5px',
                fontWeight: 500,
                fontSize: 14,
                minWidth: 120,
                px: 2,
                textTransform: 'none',
                bgcolor: '#fff',
                color: '#222',
                borderColor: '#d1d5db',
                boxShadow: 'none',
                '&:hover': {
                  bgcolor: '#f5f6fa',
                  borderColor: '#2563eb',
                  color: '#2563eb',
                },
                '&.Mui-focused, &.Mui-active': {
                  borderColor: '#2563eb',
                  color: '#2563eb',
                },
              }}
              onClick={handleHomeTypeMenuOpen}
            >
              Home Type
            </Button>
            <Menu
              anchorEl={homeTypeAnchorEl}
              open={Boolean(homeTypeAnchorEl)}
              onClose={handleHomeTypeMenuClose}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
              transformOrigin={{ vertical: 'top', horizontal: 'left' }}
              PaperProps={{
                sx: {
                  borderRadius: 3,
                  minWidth: 340,
                  p: 0,
                  boxShadow: 6,
                  mt: 1,
                }
              }}
            >
              <Box sx={{ bgcolor: '#f7f8fa', px: 3, py: 2, borderTopLeftRadius: 12, borderTopRightRadius: 12 }}>
                <Typography variant="subtitle1" fontWeight={600} color="#6e6e6e">Home Type</Typography>
              </Box>
              <Box sx={{ px: 3, pt: 2, pb: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedHomeTypes.length === homeTypeOptions.length}
                        indeterminate={selectedHomeTypes.length > 0 && selectedHomeTypes.length < homeTypeOptions.length}
                        onChange={handleDeselectAllHomeTypes}
                        sx={{ p: 0, mr: 1 }}
                      />
                    }
                    label={
                      <Typography
                        variant="subtitle1"
                        fontWeight={700}
                        sx={{ color: '#2563eb' }}
                      >
                        {selectedHomeTypes.length === homeTypeOptions.length ? 'Deselect All' : 'Select All'}
                      </Typography>
                    }
                    sx={{ ml: 0 }}
                  />
                </Box>
                {homeTypeOptions.map(opt => (
                  <Box key={opt.value} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Checkbox
                      checked={selectedHomeTypes.includes(opt.value)}
                      onChange={() => handleHomeTypeChange(opt.value)}
                      sx={{ color: '#2563eb', p: 0, mr: 1 }}
                    />
                    <Typography variant="body1" fontWeight={500}>{opt.label}</Typography>
                  </Box>
                ))}
              </Box>
              <Box sx={{ px: 3, pb: 2, pt: 1 }}>
                <Button
                  variant="contained"
                  fullWidth
                  sx={{
                    bgcolor: '#2563eb',
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: 16,
                    borderRadius: 2,
                    height: 44,
                    mt: 1,
                    textTransform: 'none',
                    boxShadow: 'none',
                    '&:hover': { bgcolor: '#1742a0' },
                  }}
                  onClick={handleApplyHomeType}
                >
                  Apply
                </Button>
              </Box>
            </Menu>
            <Button
              variant="outlined"
              endIcon={<ArrowDropDownIcon />}
              sx={{
                height: 36,
                borderRadius: '5px',
                fontWeight: 500,
                fontSize: 14,
                minWidth: 80,
                px: 2,
                textTransform: 'none',
                bgcolor: '#fff',
                color: '#222',
                borderColor: '#d1d5db',
                boxShadow: 'none',
                '&:hover': {
                  bgcolor: '#f5f6fa',
                  borderColor: '#2563eb',
                  color: '#2563eb',
                },
                '&.Mui-focused, &.Mui-active': {
                  borderColor: '#2563eb',
                  color: '#2563eb',
                },
              }}
              onClick={handleMoreMenuOpen}
            >
              More
            </Button>
            {/* Send to Cycl Sales Button (replaces Search on Market when items are selected) */}
            {selectedProperties.size > 0 ? (
              <Button
                variant="contained"
                size="small"
                sx={{
                  height: 36,
                  borderRadius: '5px',
                  bgcolor: '#2563eb',
                  color: '#fff',
                  fontWeight: 600,
                  fontSize: 14,
                  px: 2,
                  ml: 1,
                  textTransform: 'none',
                  boxShadow: 'none',
                  '&:hover': { bgcolor: '#1742a0' },
                }}
                startIcon={<SendIcon />}
                onClick={() => setShowSendToCyclSalesPopup(true)}
              >
                Send to Cycl Sales
              </Button>
            ) : (
              <Button
                variant="contained"
                size="small"
                sx={{
                  height: 36,
                  borderRadius: '5px',
                  bgcolor: '#2563eb',
                  color: '#fff',
                  fontWeight: 600,
                  fontSize: 14,
                  px: 2,
                  ml: 1,
                  textTransform: 'none',
                  boxShadow: 'none',
                  '&:hover': { bgcolor: '#1742a0' },
                }}
                onClick={() => setShowFilterSummary(true)}
              >
                Search on Market
              </Button>
            )}
            <Menu
              anchorEl={moreAnchorEl}
              open={Boolean(moreAnchorEl)}
              onClose={handleMoreMenuClose}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
              transformOrigin={{ vertical: 'top', horizontal: 'left' }}
              PaperProps={{
                sx: {
                  borderRadius: 3,
                  minWidth: 520,
                  maxWidth: 600,
                  maxHeight: 700,
                  p: 0,
                  boxShadow: 6,
                  mt: 1,
                  overflowY: 'auto',
                }
              }}
            >
              <Box sx={{ bgcolor: '#f7f8fa', px: 3, py: 2, borderTopLeftRadius: 12, borderTopRightRadius: 12 }}>
                <Typography variant="subtitle1" fontWeight={700} color="#6e6e6e">More Filters</Typography>
              </Box>
              <Box sx={{ px: 3, pt: 2, pb: 1 }}>
                {/* Square feet */}
                <Typography variant="subtitle2" fontWeight={700} mb={1}>Square feet</Typography>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <FormControl size="small" sx={{ minWidth: 120 }}>
                    <Select value={sqftMin} onChange={handleSqftMinChange} displayEmpty>
                      <MenuItem value="">No Min</MenuItem>
                      {sqftOptions.slice(1).map(val => (
                        <MenuItem key={val} value={val}>{parseInt(val).toLocaleString()}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <Typography sx={{ mx: 1, color: '#6e6e6e', alignSelf: 'center' }}>-</Typography>
                  <FormControl size="small" sx={{ minWidth: 120 }}>
                    <Select value={sqftMax} onChange={handleSqftMaxChange} displayEmpty>
                      <MenuItem value="">No Max</MenuItem>
                      {sqftOptions.slice(1).map(val => (
                        <MenuItem key={val} value={val}>{parseInt(val).toLocaleString()}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
                {/* Lot size */}
                <Typography variant="subtitle2" fontWeight={700} mb={1}>Lot size</Typography>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <FormControl size="small" sx={{ minWidth: 120 }}>
                    <Select value={lotMin} onChange={handleLotMinChange} displayEmpty>
                      <MenuItem value="">No Min</MenuItem>
                      {lotOptions.slice(1).map((val, i) => (
                        <MenuItem key={val} value={val}>{lotLabels[i + 1]}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <Typography sx={{ mx: 1, color: '#6e6e6e', alignSelf: 'center' }}>-</Typography>
                  <FormControl size="small" sx={{ minWidth: 120 }}>
                    <Select value={lotMax} onChange={handleLotMaxChange} displayEmpty>
                      <MenuItem value="">No Max</MenuItem>
                      {lotOptions.slice(1).map((val, i) => (
                        <MenuItem key={val} value={val}>{lotLabels[i + 1]}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
                {/* Year built */}
                <Typography variant="subtitle2" fontWeight={700} mb={1}>Year built</Typography>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <FormControl size="small" sx={{ minWidth: 120 }}>
                    <Select value={yearMin} onChange={handleYearMinChange} displayEmpty>
                      <MenuItem value="">No Min</MenuItem>
                      {yearOptions.slice(1).map(val => (
                        <MenuItem key={val} value={val}>{val}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <Typography sx={{ mx: 1, color: '#6e6e6e', alignSelf: 'center' }}>-</Typography>
                  <FormControl size="small" sx={{ minWidth: 120 }}>
                    <Select value={yearMax} onChange={handleYearMaxChange} displayEmpty>
                      <MenuItem value="">No Max</MenuItem>
                      {yearOptions.slice(1).map(val => (
                        <MenuItem key={val} value={val}>{val}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
                {/* Basement */}
                <Typography variant="subtitle2" fontWeight={700} mt={2}>Basement</Typography>
                <FormControlLabel control={<Checkbox checked={hasBasement} onChange={handleCheckboxChange(setHasBasement)} />} label="Has basement" />
                {/* <FormControlLabel control={<Checkbox checked={singleStory} onChange={e => setSingleStory(e.target.checked)} />} label="Single-story only" /> */}
                {/* Other Amenities */}
                <Typography variant="subtitle2" fontWeight={700} mt={2}>Other Amenities</Typography>
                <FormControlLabel control={<Checkbox checked={mustHaveAC} onChange={handleCheckboxChange(setMustHaveAC)} />} label="Must have A/C" />
                <FormControlLabel control={<Checkbox checked={mustHavePool} onChange={handleCheckboxChange(setMustHavePool)} />} label="Must have pool" />
                <FormControlLabel control={<Checkbox checked={waterfront} onChange={handleCheckboxChange(setWaterfront)} />} label="Waterfront" />
                <FormControlLabel control={<Checkbox checked={onSiteParking} onChange={handleCheckboxChange(setOnSiteParking)} />} label="On-site Parking" />
                <FormControlLabel control={<Checkbox checked={inUnitLaundry} onChange={handleCheckboxChange(setInUnitLaundry)} />} label="In-unit Laundry" />
                <FormControlLabel control={<Checkbox checked={acceptsZillowApps} onChange={handleCheckboxChange(setAcceptsZillowApps)} />} label="Accepts Zillow Applications" />
                <FormControlLabel control={<Checkbox checked={incomeRestricted} onChange={handleCheckboxChange(setIncomeRestricted)} />} label="Income restricted" />
                <FormControlLabel control={<Checkbox checked={hardwoodFloors} onChange={handleCheckboxChange(setHardwoodFloors)} />} label="Hardwood Floors" />
                <FormControlLabel control={<Checkbox checked={disabledAccess} onChange={handleCheckboxChange(setDisabledAccess)} />} label="Disabled Access" />
                <FormControlLabel control={<Checkbox checked={utilitiesIncluded} onChange={handleCheckboxChange(setUtilitiesIncluded)} />} label="Utilities Included" />
                <FormControlLabel control={<Checkbox checked={shortTermLease} onChange={handleCheckboxChange(setShortTermLease)} />} label="Short term lease available" />
                <FormControlLabel control={<Checkbox checked={furnished} onChange={handleCheckboxChange(setFurnished)} />} label="Furnished" />
                <FormControlLabel control={<Checkbox checked={outdoorSpace} onChange={handleCheckboxChange(setOutdoorSpace)} />} label="Outdoor space" />
                <FormControlLabel control={<Checkbox checked={controlledAccess} onChange={handleCheckboxChange(setControlledAccess)} />} label="Controlled access" />
                <FormControlLabel control={<Checkbox checked={highSpeedInternet} onChange={handleCheckboxChange(setHighSpeedInternet)} />} label="High speed internet" />
                <FormControlLabel control={<Checkbox checked={elevator} onChange={handleCheckboxChange(setElevator)} />} label="Elevator" />
                <FormControlLabel control={<Checkbox checked={apartmentCommunity} onChange={handleCheckboxChange(setApartmentCommunity)} />} label="Apartment Community" />
                {/* View */}
                <Typography variant="subtitle2" fontWeight={700} mt={2}>View</Typography>
                <FormControlLabel control={<Checkbox checked={viewCity} onChange={handleCheckboxChange(setViewCity)} />} label="City" />
                <FormControlLabel control={<Checkbox checked={viewMountain} onChange={handleCheckboxChange(setViewMountain)} />} label="Mountain" />
                <FormControlLabel control={<Checkbox checked={viewPark} onChange={handleCheckboxChange(setViewPark)} />} label="Park" />
                <FormControlLabel control={<Checkbox checked={viewWater} onChange={handleCheckboxChange(setViewWater)} />} label="Water" />
                {/* Commute Time */}
                {/* <Typography variant="subtitle2" fontWeight={700} mt={2}>Commute Time</Typography>
                <TextField
                  placeholder="Enter address, city, state and ZIP code"
                  value={commute}
                  onChange={e => setCommute(e.target.value)}
                  size="small"
                  fullWidth
                  sx={{ mb: 2 }}
                /> */}
                {/* Days on Zillow */}
                <Typography variant="subtitle2" fontWeight={700} mt={2}>Days on Zillow</Typography>
                <FormControl size="small" fullWidth sx={{ mb: 2 }}>
                  <Select value={daysOnZillow} onChange={e => setDaysOnZillow(e.target.value)} displayEmpty>
                    <MenuItem value="">Any</MenuItem>
                    <MenuItem value="1">1</MenuItem>
                    <MenuItem value="7">7</MenuItem>
                    <MenuItem value="14">14</MenuItem>
                    <MenuItem value="30">30</MenuItem>
                    <MenuItem value="90">90</MenuItem>
                  </Select>
                </FormControl>
                {/* Keywords */}
                <Typography variant="subtitle2" fontWeight={700} mt={2}>Keywords</Typography>
                <TextField
                  placeholder="Short term, furnished, etc."
                  value={keywords}
                  onChange={e => setKeywords(e.target.value)}
                  size="small"
                  fullWidth
                  sx={{ mb: 2 }}
                />
                {/* 55+ Communities */}
                {/* <Box sx={{ display: 'flex', alignItems: 'center', mt: 2, mb: 1 }}>
                  <Typography variant="subtitle2" fontWeight={700} mr={1}>55+ Communities</Typography>
                  <Box sx={{ bgcolor: '#fee2e2', color: '#b91c1c', fontWeight: 700, fontSize: 12, borderRadius: 1, px: 1, py: 0.2, ml: 1 }}>NEW</Box>
                </Box>
                <RadioGroup value={fiftyFivePlus} onChange={e => setFiftyFivePlus(e.target.value)}>
                  <FormControlLabel value="include" control={<Radio sx={{ color: '#2563eb', '&.Mui-checked': { color: '#2563eb' } }} />} label="Include" />
                  <FormControlLabel value="dont_show" control={<Radio sx={{ color: '#2563eb', '&.Mui-checked': { color: '#2563eb' } }} />} label="Don't show" />
                  <FormControlLabel value="only_show" control={<Radio sx={{ color: '#2563eb', '&.Mui-checked': { color: '#2563eb' } }} />} label="Only show" />
                </RadioGroup> */}
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', px: 3, py: 2, borderBottomLeftRadius: 12, borderBottomRightRadius: 12, bgcolor: '#fff', borderTop: '1px solid #e0e0e0' }}>
                <Button
                  onClick={handleResetAllFilters}
                  sx={{ color: '#2563eb', fontWeight: 700, fontSize: 16, textTransform: 'none' }}
                >
                  Reset all filters
                </Button>
                <Button
                  variant="contained"
                  sx={{
                    bgcolor: '#2563eb',
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: 16,
                    borderRadius: 2,
                    height: 44,
                    minWidth: 120,
                    textTransform: 'none',
                    boxShadow: 'none',
                    '&:hover': { bgcolor: '#1742a0' },
                  }}
                  onClick={handleApplyMore}
                >
                  Apply
                </Button>
              </Box>
            </Menu>
          </Box>

          {/* Filter and PageSizeSelector Row */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            {/* <Button
              variant="outlined"
              startIcon={<TuneIcon />}
              sx={{
                borderRadius: '5px',
                fontWeight: 600,
                fontSize: 14,
                px: 1.5,
                py: 0.5,
                minHeight: 32,
                height: 32,
                textTransform: 'none',
                bgcolor: '#fff',
                color: '#222',
                borderColor: '#d1d5db',
                boxShadow: 'none',
                '&:hover': {
                  bgcolor: '#f5f6fa',
                  borderColor: '#2563eb',
                  color: '#2563eb',
                },
              }}
              onClick={e => setFilterAnchorEl(e.currentTarget)}
            >
              Filter
            </Button> */}
            <PageSizeSelector
              totalResults={totalResults}
              pageSize={pageSize}
              page={page}
              onPageSizeChange={(newSize) => {
                setPageSize(newSize);
                setPage(1);
                // Only fetch if not loading and only for current data source
                if (!loading) {
                  if (dataSource === 'db' && !hasSearched) {
                    if (!locationId) return; // Do not fetch if locationId is not set
                    fetchProperties('db', 1, newSize);
                  }
                  if (dataSource === 'market' && hasSearched) fetchProperties('market', 1, newSize);
                }
              }}
              loading={loading}
            />
          </Box>

          <Box sx={{ width: '100%', mt: 4 }}>
            {/* Error Message */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            <TableContainer component={Paper} sx={{ width: '100%', borderRadius: 4, boxShadow: 2, overflowX: 'auto' }}>
              <Table sx={{ minWidth: 700, maxWidth: '100%' }}>
                <TableHead>
                  {/* Filter button above the table, outside the table, smaller and less rounded */}
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedProperties.size === properties.length && properties.length > 0}
                        indeterminate={selectedProperties.size > 0 && selectedProperties.size < properties.length}
                        onChange={handleSelectAll}
                      />
                    </TableCell>
                    <TableCell>Image</TableCell>
                    <TableCell onClick={() => handleSort('address')} sx={{ cursor: 'pointer', userSelect: 'none' }}>
                      Address {sortColumn === 'address' && (sortDirection === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />)}
                    </TableCell>
                    <TableCell onClick={() => handleSort('price')} sx={{ cursor: 'pointer', userSelect: 'none' }}>
                      Price {sortColumn === 'price' && (sortDirection === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />)}
                    </TableCell>
                    <TableCell onClick={() => handleSort('bedrooms')} sx={{ cursor: 'pointer', userSelect: 'none' }}>
                      Beds {sortColumn === 'bedrooms' && (sortDirection === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />)}
                    </TableCell>
                    <TableCell onClick={() => handleSort('bathrooms')} sx={{ cursor: 'pointer', userSelect: 'none' }}>
                      Baths {sortColumn === 'bathrooms' && (sortDirection === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />)}
                    </TableCell>
                    <TableCell onClick={() => handleSort('living_area')} sx={{ cursor: 'pointer', userSelect: 'none' }}>
                      Sq Ft {sortColumn === 'living_area' && (sortDirection === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />)}
                    </TableCell>
                    <TableCell onClick={() => handleSort('type')} sx={{ cursor: 'pointer', userSelect: 'none' }}>
                      Type {sortColumn === 'type' && (sortDirection === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />)}
                    </TableCell>
                    <TableCell onClick={() => handleSort('status')} sx={{ cursor: 'pointer', userSelect: 'none' }}>
                      Status {sortColumn === 'status' && (sortDirection === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />)}
                    </TableCell>
                    <TableCell onClick={() => handleSort('sent_to_cyclsales_count')} sx={{ cursor: 'pointer', userSelect: 'none' }}>
                      Sent to CS {sortColumn === 'sent_to_cyclsales_count' && (sortDirection === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />)}
                    </TableCell>
                    <TableCell onClick={() => handleSort('listingAgent')} sx={{ cursor: 'pointer', userSelect: 'none' }}>
                      Listing Agent {sortColumn === 'listingAgent' && (sortDirection === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />)}
                    </TableCell>
                  </TableRow>
                </TableHead>
                {loading ? (
                  <TableSkeleton rows={pageSize} />
                ) : (
                  <TableBody>
                    {sortedProperties.length > 0 ? (
                      sortedProperties.map((prop, _) => (
                        <TableRow
                          key={prop.id}
                          hover
                          selected={Array.isArray(selectedProperties) && selectedProperties.includes(String(prop.id ?? ''))}
                          className={fadingProperties.has(String(prop.id || '')) ? 'fade-out' : ''}
                          style={{ transition: 'opacity 0.5s', opacity: fadingProperties.has(String(prop.id || '')) ? 0 : 1 }}
                        >
                          <TableCell padding="checkbox">
                            <Checkbox
                              checked={selectedProperties.has(String(prop.id || ''))}
                              onChange={() => handleSelectProperty(String(prop.id || ''))}
                            />
                          </TableCell>
                          <TableCell>
                            {prop.hi_res_image_link ? (
                              <Box
                                component="img"
                                src={prop.hi_res_image_link}
                                alt={prop.street_address}
                                sx={{
                                  width: 100,
                                  height: 75,
                                  objectFit: 'cover',
                                  borderRadius: 1,
                                }}
                              />
                            ) : (
                              <Box
                                sx={{
                                  width: 100,
                                  height: 75,
                                  bgcolor: 'grey.200',
                                  borderRadius: 1,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                }}
                              >
                                <Typography variant="caption" color="text.secondary">
                                  No image
                                </Typography>
                              </Box>
                            )}
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="text"
                              sx={{
                                color: 'primary.main',
                                textAlign: 'left',
                                textTransform: 'none',
                                p: 0,
                                minWidth: 0,
                                '&:hover': { textDecoration: 'underline', background: 'none' },
                                display: 'block',
                                width: '100%',
                                alignItems: 'flex-start',
                              }}
                              onClick={() => setSelectedZpid(prop.zpid || null)}
                            >
                              <Typography variant="subtitle2" sx={{ display: 'block', lineHeight: 1.2 }}>
                                {prop.street_address}
                              </Typography>
                              <Typography variant="body2" color="text.secondary" sx={{ display: 'block', lineHeight: 1.2 }}>
                                {`${prop.city}, ${prop.state}${(prop.zip_code || prop.zipcode) ? ' ' + (prop.zip_code || prop.zipcode) : ''}`}
                              </Typography>
                            </Button>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={`$${prop.price?.toLocaleString() || 'N/A'}`}
                              color="primary"
                            />
                          </TableCell>
                          <TableCell>
                            {prop.bedrooms ? <Chip
                              label={prop.bedrooms}
                              sx={{ bgcolor: '#10b981', color: '#fff' }}
                            /> : <Typography variant="body2" color="text.secondary" sx={{
                              textAlign: 'center',
                            }}>--</Typography>}
                          </TableCell>
                          <TableCell>
                            {prop.bathrooms ? <Chip
                              label={prop.bathrooms}
                              sx={{ bgcolor: '#f59e42', color: '#fff' }}
                            /> : <Typography variant="body2" color="text.secondary" sx={{
                              textAlign: 'center',
                            }}>--</Typography>}
                          </TableCell>
                          <TableCell>
                            {prop.living_area?.toLocaleString() || 'N/A'}
                          </TableCell>
                          <TableCell>{prop.home_type || 'N/A'}</TableCell>
                          <TableCell>
                            <Chip
                              label={prop.home_status || 'N/A'}
                              sx={{
                                bgcolor: prop.home_status === 'Active' ? '#22c55e' : '#64748b',
                                color: '#fff',
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            {prop.sent_to_cyclsales ? (
                              <Chip
                                label="Sent"
                                sx={{ bgcolor: '#22c55e', color: '#fff', fontWeight: 600 }}
                                size="small"
                              />
                            ) : (
                              <Chip
                                label="Not Sent"
                                sx={{ bgcolor: '#64748b', color: '#fff', fontWeight: 600 }}
                                size="small"
                              />
                            )}
                          </TableCell>
                          <TableCell>
                            {prop.listingAgent && prop.listingAgent.name ? (
                              <Box sx={{ lineHeight: 1.2 }}>
                                <Typography variant="subtitle2">{prop.listingAgent.name}</Typography>
                                {prop.listingAgent.email && (
                                  <Typography variant="body2" color="text.secondary">{prop.listingAgent.email}</Typography>
                                )}
                                {prop.listingAgent.phone && (
                                  <Typography variant="body2" color="text.secondary">{prop.listingAgent.phone}</Typography>
                                )}
                              </Box>
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                No agent info
                              </Typography>
                            )}
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={10} align="center">
                          <Typography variant="body1" color="text.secondary">
                            No properties found
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                )}
              </Table>
            </TableContainer>
          </Box>

          {/* Pagination */}
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mt: 4, gap: 2 }}>
            <Pagination
              count={Math.ceil(totalResults / pageSize)}
              page={page}
              onChange={handlePageChange}
              color="primary"
              showFirstButton
              showLastButton
            />
            <FormControl size="small" sx={{ minWidth: 80 }}>
              <Select value={pageSize} onChange={e => { setPageSize(Number(e.target.value)); setPage(1); if (hasSearched) fetchProperties('db', 1, Number(e.target.value)); }}>
                {pageSizeOptions.map(size => (
                  <MenuItem key={size} value={size}>{size} / page</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>
      </Box>
      <PropertyPopup
        zpid={selectedZpid}
        isOpen={!!selectedZpid}
        onClose={() => setSelectedZpid(null)}
        viewOnMarketUrl={selectedZpid ? `https://www.zillow.com/homes/${selectedZpid}_zpid/` : undefined}
      />
      {/* Send to Cycl Sales Popup */}
      {showSendToCyclSalesPopup && (
        <Dialog open={showSendToCyclSalesPopup} onClose={() => !loadingSendToCS && setShowSendToCyclSalesPopup(false)}>
          <DialogTitle>Send to Cycl Sales</DialogTitle>
          <DialogContent>
            <Typography>Are you sure you want to send the selected properties to Cycl Sales?</Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowSendToCyclSalesPopup(false)} color="secondary" disabled={loadingSendToCS}>Cancel</Button>
            <Button onClick={handleSendToCyclSales} color="primary" variant="contained" disabled={loadingSendToCS} startIcon={loadingSendToCS ? <CircularProgress size={18} /> : <SendIcon />}>
              {loadingSendToCS ? 'Sending...' : 'Send'}
            </Button>
          </DialogActions>
        </Dialog>
      )}
      {/* Filter Summary Dialog */}
      <FilterSummaryDialog
        open={showFilterSummary}
        onClose={() => setShowFilterSummary(false)}
        onContinue={async () => {
          setShowFilterSummary(false);
          await handleSearchOnZillow();
        }}
        filters={getCurrentFilters()}
      />
      {/* Add fade-out CSS */}
      <style>{`
      .fade-out {
        opacity: 0 !important;
        transition: opacity 0.5s !important;
      }
      `}</style>
      {backgroundFetching && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <CircularProgress size={18} color="primary" />
          <Typography variant="body2" color="text.secondary">
            Fetching new properties in the background...
          </Typography>
        </Box>
      )}
    </ThemeProvider>
  );
}

export default App;
