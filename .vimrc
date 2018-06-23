set modeline
set modelines=3
set expandtab
set hlsearch
set ai
set autowrite

syntax on
filetype plugin on
colorscheme murphy

set tabstop=4
set softtabstop=4
set shiftwidth=4

autocmd FileType yaml set tabstop=2
autocmd FileType yaml set softtabstop=2
autocmd FileType yaml set shiftwidth=2

autocmd FileType coffee set tabstop=2
autocmd FileType coffee set softtabstop=2
autocmd FileType coffee set shiftwidth=2

syntax enable
filetype plugin indent on
