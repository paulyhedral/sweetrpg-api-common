// swift-tools-version:5.4

import PackageDescription


let package = Package(
        name: "sweetrpg-api-common",
        platforms: [
            .macOS(.v10_15),
        ],
        products: [
            .library(name: "APICommon", targets: [ "APICommon" ]),
        ],
        dependencies: [
            // 💧 A server-side Swift web framework.
            .package(url: "https://github.com/vapor/vapor.git", from: "4.0.0"),
            .package(url: "https://github.com/vapor/fluent.git", from: "4.0.0"),
//            .package(url: "https://github.com/vapor/fluent-mongo-driver.git", from: "1.0.0"),
//            .package(url: "https://github.com/vapor/leaf.git", from: "4.0.0"),
//            .package(url: "https://github.com/vapor/jwt.git", from: "4.0.0"),
//            .package(url: "https://github.com/vapor-community/sendgrid.git", from: "4.0.0"),
//            .package(url: "https://github.com/vapor/redis.git", from: "4.0.0"),
            // .package(name: "sweetrpg-users-model", path: "../UsersModel"),
        ],
        targets: [
            .target(
                    name: "APICommon",
                    dependencies: [
                        .product(name: "Fluent", package: "fluent"),
                        .product(name: "Vapor", package: "vapor"),
                    ],
                    swiftSettings: [
                        // Enable better optimizations when building in Release configuration. Despite the use of
                        // the `.unsafeFlags` construct required by SwiftPM, this flag is recommended for Release
                        // builds. See <https://github.com/swift-server/guides/blob/main/docs/building.md#building-for-production> for details.
                        .unsafeFlags([ "-cross-module-optimization" ], .when(configuration: .release)),
                    ]
            ),
            .testTarget(name: "APICommonTests", dependencies: [
                .target(name: "APICommon"),
                .product(name: "XCTVapor", package: "vapor"),
            ]),
        ]
)
