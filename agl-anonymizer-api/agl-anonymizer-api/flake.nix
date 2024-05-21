{
  description = "A flake for a Django API with agl-anonymizer app";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    # You can add other inputs if needed
  };

  outputs = { self, nixpkgs, flake-utils, cachix }: 
  let
    system = "x86_64-linux"; # Adjust to your system architecture
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
          # Call with nix develop
          devShell."${system}" = pkgs.mkShell {
            buildInputs = with pkgs; [ 
              poetry
              autoAddDriverRunpath

              # CUDA
              # cudatoolkit
              # cudaPackages.cudnn
              cudaPackages.cudatoolkit 
              # linuxPackages.nvidia_x11
              # cudaPackages.cudnn

              libGLU libGL
              glibc
              xorg.libXi xorg.libXmu freeglut
              xorg.libXext xorg.libX11 xorg.libXv xorg.libXrandr zlib 
              ncurses5 stdenv.cc binutils
              gcc

              python311
	            python311Packages.dulwich
              python311Packages.venvShellHook

              pam

            ];

            # Define Environment Variables
            DJANGO_SETTINGS_MODULE="agl-anonymizer-api.settings";

            # Define Python venv
            venvDir = ".venv";
            postShellHook = ''
              export CUDA_PATH=${pkgs.cudatoolkit}
              export LD_LIBRARY_PATH=${pkgs.linuxPackages.nvidia_x11}/lib
              export EXTRA_LDFLAGS="-L/lib -L${pkgs.linuxPackages.nvidia_x11}/lib"
              export EXTRA_CCFLAGS="-I/usr/include"
              
              python -m pip install --upgrade pip
              poetry update

            '';
          };

        nixConfig = {
          binary-caches = [nvidiaCache.binaryCachePublicUrl];
          binary-cache-public-keys = [nvidiaCache.publicKey];
        };
      };
}