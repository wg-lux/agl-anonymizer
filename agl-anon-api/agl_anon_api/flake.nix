{
  description = "A flake for a Django API with agl_anonymizer app";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    # You can add other inputs if needed
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux"; # Adjust to your system architecture
    pkgs = import nixpkgs { inherit system; };
  in {
    packages = {
      # Define your Django package
      django = pkgs.mkShell {
        buildInputs = [
          pkgs.python3
          pkgs.python3Packages.django
          pkgs.python3Packages.gunicorn
          pkgs.python3Packages.pillow
          pkgs.python3Packages.requests
          pkgs.python3Packages.django-cors-headers
          # Add other Python packages required by your project
        ];

        shellHook = ''
          # Activate virtual environment if necessary
          echo "Entering Django development shell"
        '';
      };
    };

    devShells = {
      default = pkgs.mkShell {
        buildInputs = [
          pkgs.python3
          pkgs.python3Packages.django
          pkgs.python3Packages.gunicorn
          pkgs.python3Packages.pillow
          pkgs.python3Packages.requests
          pkgs.python3Packages.django-cors-headers
          # Add other Python packages required by your project
        ];

        shellHook = ''
          echo "Entering Django development shell"
          export DJANGO_SETTINGS_MODULE=myproject.settings
        '';
      };
    };

    # You can define other outputs like apps, overlays, etc.
  };
}
