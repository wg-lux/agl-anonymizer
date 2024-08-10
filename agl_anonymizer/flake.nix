{
  description = "Python application agl_anonymizer packaged using poetry2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
  };

  outputs = { self, nixpkgs, poetry2nix, ... }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
      config.allowUnfree = true;
      config.cudaSupport = true;
    };
  in
  {
    devShell.${system} = pkgs.mkShell {
      buildInputs = with pkgs; [
        poetry
        stdenv.cc.cc.lib
        cudaPackages.cudatoolkit
        libGLU
        libGL
        glibc
        zlib
        glib
        xorg.libXi
        xorg.libXmu
        freeglut
        xorg.libXext
        xorg.libX11
        xorg.libXv
        xorg.libXrandr
        ncurses5
        stdenv.cc
        binutils
        gcc11
        opencv4
        
        cudaPackages.cudnn
        cudaPackages.cudatoolkit 
        linuxPackages.nvidia_x11
        libGLU libGL
        xorg.libXi xorg.libXmu freeglut
        xorg.libXext xorg.libX11 xorg.libXv xorg.libXrandr zlib 
        ncurses5 stdenv.cc binutils
        python311
        python311Packages.venvShellHook
        python311Packages.numpy
        python311Packages.torchvision-bin
        python311Packages.torchaudio-bin
        python311
        python311Packages.setuptools
        python311Packages.gensim
        python311Packages.scipy
        python311Packages.dulwich
        python311Packages.pandas
        python311Packages.pytesseract
        python311Packages.venvShellHook
        python311Packages.numpy
        python311Packages.imutils
        pam

        autoAddDriverRunpath

        libGLU libGL
        glibc
        xorg.libXi xorg.libXmu freeglut
        xorg.libXext xorg.libX11 xorg.libXv xorg.libXrandr zlib
        ncurses5 stdenv.cc binutils
        gcc

        python311Packages.pip
        python311Packages.djangorestframework-guardian2
        python311Packages.django-cors-headers
        python311Packages.pillow
        python311Packages.requests
        python311Packages.gunicorn
        python311Packages.psycopg2
        nginx

        # Referencing the submodule's devShell

        pam
      ];
      venvDir = ".venv";
      postShellHook = ''
        export CUDA_PATH=${pkgs.cudaPackages.cudatoolkit}
        export LD_LIBRARY_PATH="${pkgs.linuxPackages.nvidia_x11}/lib:${pkgs.zlib}/lib:${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.libGL}/lib:${pkgs.libGLU}/lib:${pkgs.glib}/lib:${pkgs.glibc}/lib:/nix/store/3xsbahrqqc4fc3gknmjj9j9687n4hiz0-glib-2.80.0/lib/:$LD_LIBRARY_PATH"
        export EXTRA_LDFLAGS="-L/lib -L${pkgs.linuxPackages.nvidia_x11}/lib"
        export EXTRA_CCFLAGS="-I/usr/include"
        export CUDA_NVCC_FLAGS="--compiler-bindir=$(which gcc)"
        python -m pip install --upgrade pip
        poetry install
      '';
    };


  };
}