package util

import (
	"unsafe"

	"go.mongodb.org/mongo-driver/bson"
)

func ConvertQueryParams(params QueryParams) (filter bson.D, sort bson.D, projection bson.D) {

	for _, v := range params.Filter {
		filter = append(filter, bson.E{v.Field, v.Operation})
	}

	for _, v := range params.Sort {
		sort = append(sort, bson.E{v.Field, v.Order})
	}

	for _, v := range params.Projection {
		projection = append(projection, bson.E{v.Field, *(*int)(unsafe.Pointer(&v.Inclusion)) & 1})
	}

	return
}
