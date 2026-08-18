// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "TembelCore",
    platforms: [
        .iOS(.v26),
        .macOS(.v26)
    ],
    products: [
        .library(name: "TembelCore", targets: ["TembelCore"])
    ],
    targets: [
        .target(
            name: "TembelCore",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        .testTarget(
            name: "TembelCoreTests",
            dependencies: ["TembelCore"],
            swiftSettings: [.swiftLanguageMode(.v6)]
        )
    ]
)
