call plug#begin('~/.local/share/nvim/plugged')

Plug 'sheerun/vim-polyglot'
Plug 'junegunn/vim-easy-align'
Plug 'tpope/vim-fugitive'
Plug 'tpope/vim-surround'
Plug 'scrooloose/nerdtree'
  let g:NERDTreeQuitOnOpen=1
  let g:NERDTreeChDirMode=2
Plug 'preservim/nerdcommenter'
Plug 'Shougo/deoplete.nvim', { 'do': ':UpdateRemotePlugins' }
  let g:deoplete#enable_at_startup=1
Plug 'deoplete-plugins/deoplete-jedi'
Plug 'deoplete-plugins/deoplete-clang'
  let g:deoplete#sources#clang#libclang_path='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/libclang.dylib'
  let g:deoplete#sources#clang#clang_header='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/clang/'
Plug 'Shougo/neoinclude.vim'
Plug 'drewtempelmeyer/palenight.vim'
  let g:palenight_terminal_italics=1
Plug 'sonph/onehalf', {'rtp': 'vim/'}
Plug 'arcticicestudio/nord-vim'
Plug 'ayu-theme/ayu-vim'

Plug 'ervandew/supertab'
  let g:SuperTabDefaultCompletionType='<c-n>'
"Plug 'psf/black'
  "let g:black_linelength=120
  "let g:black_skip_string_normalization=1
Plug 'vim-ctrlspace/vim-ctrlspace'
  let g:CtrlSpaceDefaultMappingKey = '<c-space> '
  set showtabline=0
  nmap <nul> :CtrlSpace<cr>
Plug 'vim-airline/vim-airline'
Plug 'vim-airline/vim-airline-themes'
  let g:airline_giu_mode=1
  let g:airline_powerline_fonts = 1
Plug 'luochen1990/rainbow'
  let g:rainbow_active=1
Plug 'mattn/emmet-vim'
Plug 'junegunn/fzf', { 'do': { -> fzf#install() } }
Plug 'junegunn/fzf.vim'
" Initialize plugin system
call plug#end()
set nocompatible
set hidden

set keymap=russian-jcukenwin
set iminsert=0
set imsearch=0
highlight lCursor guifg=NONE guibg=Cyan
"spell spelllang=ru_yo,en_us

set termguicolors
set number
set colorcolumn=120
set list
set listchars=tab:▸\ ,trail:·,extends:❯,precedes:❮,nbsp:×
set wrap
set linebreak
set autoindent
set smartindent
set shiftwidth=4
set expandtab
set tabstop=4
set softtabstop=4

let mapleader=','

nmap <silent> <leader>d <Plug>DashSearch
nmap <backspace> :NERDTreeToggle<cr>
nnoremap <silent> <esc> :nohlsearch<cr>

" Navigate through wrapped lines
noremap j gj
noremap k gk

" disable arrow keys
inoremap <Up> <NOP>
inoremap <Down> <NOP>
inoremap <Left> <NOP>
inoremap <Right> <NOP>
noremap <Up> <NOP>
noremap <Down> <NOP>
noremap <Left> <NOP>
noremap <Right> <NOP>

" Navigate with <Ctrl>-hjkl in Insert mode
inoremap <C-h> <C-o>h
inoremap <C-j> <C-o>j
inoremap <C-k> <C-o>k
inoremap <C-l> <C-o>l

" Search matches are always in center
nnoremap n nzz
nnoremap N Nzz
nnoremap * *zz
nnoremap # #zz
nnoremap g* g*zz
nnoremap g# g#zz

" autoreload
set autoread
au FocusGained * :checktime

let ayucolor='light'
let g:airline_theme='ayu'
let s:mode = systemlist("defaults read -g AppleInterfaceStyle")[0]
if s:mode ==? "dark"
    let ayucolor='mirage'
    let g:airline_theme='ayu_mirage'
endif
colorscheme ayu

