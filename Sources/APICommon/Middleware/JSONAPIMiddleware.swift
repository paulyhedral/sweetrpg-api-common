//
//  VolumesController.swift
//  Library API
//
//  Created by Paul Schifferer on 4/22/17.
//  Copyright © 2021 SweetRPG. All rights reserved.
//

import Vapor


public final class JSONAPIMiddleware : Middleware {

    public init() {
    }

    public func respond(to request : Request, chainingTo next : Responder) -> EventLoopFuture<Response> {
        return next.respond(to: request).map { response in
            return response
        }
    }

}
