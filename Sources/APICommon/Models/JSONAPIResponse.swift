//
// JSONAPIResponse.swift
//

import Vapor
import Fluent


public struct JSONAPIResponse<T> : Content where T : Content {
    public var links : Links?
    public var data : T

    public init(links : Links, data : T) {
        self.links = links
        self.data = data
    }

public struct Links : Content {
    public var current : String?
    public var next : String?
    public var last : String?
}
}
