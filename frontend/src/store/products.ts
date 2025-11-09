import { create } from 'zustand';
import { mountStoreDevtool } from 'simple-zustand-devtools';

// import { useProd}
import type { ProductType } from '../types/ProductType';

interface ProductStore {
  allProducts: ProductType[] | null;
  filteredProducts: ProductType[];
  loading: boolean;
  searchTerm: string;

  setProducts: (products: ProductType[]) => void;

  setLoading: (loading: boolean) => void;
  setSearchTerm: (term: string) => void;
  searchProducts: () => void;
  resetSearch: () => void;
}

const useProductStore = create<ProductStore>((set, get) => ({
  allProducts: null,
  filteredProducts: [],
  loading: false,
  searchTerm: '',

  // setProducts: (products) => set({ allProducts: products, filteredProducts: products }),
  setProducts: (products: ProductType[]) => {
    console.log('Setting products:', products.length);
    set({ allProducts: products, filteredProducts: products });
  },
  setLoading: (loading) => set({ loading }),
  setSearchTerm: (term) => set({ searchTerm: term }),

  searchProducts: () => {
  const term = get().searchTerm.toLowerCase();
  const all = get().allProducts || [];

  const filtered = all.filter(p => {
  return (
    typeof p.title === 'string' && p.title.toLowerCase().includes(term) ||
    typeof p.description === 'string' && p.description.toLowerCase().includes(term) ||
    typeof p.brand === 'string' && p.brand.toLowerCase().includes(term) ||
    typeof p.category === 'string' && p.category.toLowerCase().includes(term)
  );
});


  set({ filteredProducts: filtered });
},


  resetSearch: () => {
    set({ searchTerm: '', filteredProducts: get().allProducts || [] });
  },
}));

if (import.meta.env.DEV) {
  mountStoreDevtool('ProductStore', useProductStore);
}

export { useProductStore };
