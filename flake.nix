{
  description = "Python/SVG/Video environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs }: {
    devShells.x86_64-linux.default =
      let
        pkgs = import nixpkgs { system = "x86_64-linux"; };

        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          pillow
          imageio
          numpy
        ]);

      in pkgs.mkShell {
        packages = [
          pythonEnv
          pkgs.ffmpeg
          pkgs.resvg
          pkgs.fira-code
          pkgs.dejavu_fonts
        ];

      };
  };
}
