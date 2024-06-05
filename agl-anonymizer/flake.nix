{
  description = "A flake for a Django API with agl-anonymizer app";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix.url = "github:nix-community/poetry2nix";
    cachix.url = "github:cachix/cachix";
    agl_anonymizer = {
      url = "path:./agl-anonymizer-api/agl_anonymizer/agl_anonymizer";
      flake = true;
    };
  };

  outputs = { self, nixpkgs, poetry2nix, cachix, agl_anonymizer, ... }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
      config.allowUnfree = true;
      config.cudaSupport = true;
    };
    nvidiaCache = cachix.lib.mkCachixCache {
      inherit (pkgs) lib;
      name = "nvidia";
      publicKey = "nvidia.cachix.org-1:dSyZxI8geDCJrwgvBfPH3zHMC+PO6y/BT7O6zLBOv0w=";
      secretKey = null;  # not needed for pulling from the cache
    };
  in
  {
    devShell.${system} = pkgs.mkShell {
      buildInputs = with pkgs; [
        poetry
        autoAddDriverRunpath

        # CUDA
        cudaPackages.cudatoolkit

        libGLU libGL
        glibc
        xorg.libXi xorg.libXmu freeglut
        xorg.libXext xorg.libX11 xorg.libXv xorg.libXrandr zlib
        ncurses5 stdenv.cc binutils
        gcc

        python311
        python311Packages.dulwich
        python311Packages.venvShellHook
        python311Packages.pip
        python311Packages.djangorestframework-guardian2
        python311Packages.django-cors-headers
        python311Packages.pillow
        python311Packages.requests
        python311Packages.gunicorn
        python311Packages.psycopg2
        nginx

        # Referencing the submodule's devShell
        (import agl_anonymizer).devShell.${system}

        pam
      ];

      # Define Environment Variables
      DJANGO_SETTINGS_MODULE="agl-anonymizer-api.settings";
      
      # Define Python venv
      venvDir = ".venv";

      shellHook = ''
        echo "Current directory before direnv allow: $(pwd)"
        # Ensure poetry is installed and in PATH
        export PATH="$HOME/.poetry/bin:$PATH"
        direnv allow
        echo "Current directory after direnv allow: $(pwd)"
      '';

      postShellHook = ''
        export CUDA_PATH=${pkgs.cudaPackages.cudatoolkit}
        export LD_LIBRARY_PATH="${pkgs.linuxPackages.nvidia_x11}/lib:${pkgs.zlib}/lib:${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.libGL}/lib:${pkgs.libGLU}/lib:${pkgs.glib}/lib:${pkgs.glibc}/lib:/nix/store/3xsbahrqqc4fc3gknmjj9j9687n4hiz0-glib-2.80.0/lib/:$LD_LIBRARY_PATH"
        export EXTRA_LDFLAGS="-L/lib -L${pkgs.linuxPackages.nvidia_x11}/lib"
        export EXTRA_CCFLAGS="-I/usr/include"
        print("file paths set")

        # Ensure no duplicate settings for compiler-bindir
        export CUDA_NVCC_FLAGS="--compiler-bindir=$(which gcc)"

        poetry install # Ensure poetry dependencies are installed
      '';
    };

    nixConfig = {
      binary-caches = [nvidiaCache.binaryCachePublicUrl];
      binary-cache-public-keys = [nvidiaCache.publicKey];
    };
  };
}
