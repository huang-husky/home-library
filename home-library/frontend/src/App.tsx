import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HomePage } from './pages/Home';
import { LibraryPage } from './pages/Library';
import { BookAddPage } from './pages/BookAdd';
import { BookDetailPage } from './pages/BookDetail';
import { BookshelvesPage } from './pages/Bookshelves';
import { MetadataSearchPage } from './pages/MetadataSearch';
import ShelfScan from './pages/ShelfScan';
import RecognitionReview from './pages/RecognitionReview';
import { BookshelfVisualizationPage } from './pages/BookshelfVisualization';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

function Navbar() {
  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <Link to="/" className="flex items-center text-xl font-bold text-blue-600">
              HomeLib
            </Link>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <Link
                to="/"
                className="inline-flex items-center px-1 pt-1 text-gray-900 hover:text-gray-700"
              >
                首页
              </Link>
              <Link
                to="/library"
                className="inline-flex items-center px-1 pt-1 text-gray-500 hover:text-gray-700"
              >
                图书馆
              </Link>
              <Link
                to="/metadata/search"
                className="inline-flex items-center px-1 pt-1 text-gray-500 hover:text-gray-700"
              >
                搜索图书
              </Link>
              <Link
                to="/bookshelves"
                className="inline-flex items-center px-1 pt-1 text-gray-500 hover:text-gray-700"
              >
                书柜
              </Link>
              <Link
                to="/scan"
                className="inline-flex items-center px-1 pt-1 text-gray-500 hover:text-gray-700"
              >
                扫描
              </Link>
              <Link
                to="/review"
                className="inline-flex items-center px-1 pt-1 text-gray-500 hover:text-gray-700"
              >
                审核
              </Link>
              <Link
                to="/bookshelf-visualization"
                className="inline-flex items-center px-1 pt-1 text-gray-500 hover:text-gray-700"
              >
                可视化
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/library" element={<LibraryPage />} />
              <Route path="/books/add" element={<BookAddPage />} />
              <Route path="/books/:id" element={<BookDetailPage />} />
              <Route path="/bookshelves" element={<BookshelvesPage />} />
              <Route path="/metadata/search" element={<MetadataSearchPage />} />
              <Route path="/scan" element={<ShelfScan />} />
              <Route path="/review" element={<RecognitionReview />} />
              <Route path="/bookshelf-visualization" element={<BookshelfVisualizationPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
