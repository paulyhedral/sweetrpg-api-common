package util

import (
	"math"

	"github.com/sweetrpg/api-core/constants"
	"github.com/sweetrpg/common/logging"
	dbconstants "github.com/sweetrpg/db/constants"
	options "go.jtlabs.io/query"
)

type Sort struct {
	Field string
	Order int
}

type Filter struct {
	Field     string
	Operation interface{}
}

type Projection struct {
	Field     string
	Inclusion bool
}

type QueryParams struct {
	Start      int64
	Limit      int
	Sort       []Sort
	Filter     []Filter
	Projection []Projection
}

func GetQueryParams(query string) QueryParams {
	logging.Logger.Debug("parsing query string", "query", query)

	opt, _ := options.FromQuerystring(query)
	logging.Logger.Debug("options from query string", "opt", opt)

	var sortFields []Sort // bson.D
	for _, v := range opt.Sort {
		sortFields = append(sortFields, Sort{v, 1} /*bson.E{v, 1}*/)
	}

	var filters []Filter // bson.D
	for k, v := range opt.Filter {
		filters = append(filters, Filter{k, v} /*bson.E{k, v}*/)
	}

	var proj []Projection // bson.D
	for _, v := range opt.Fields {
		proj = append(proj, Projection{v, true} /*bson.E{v, 1}*/)
	}

	params := QueryParams{
		Start:      int64(math.Max(0, float64(opt.Page[constants.PageStartOption]))),
		Limit:      int(math.Max(1, math.Min(float64(dbconstants.QueryMaxSize), float64(opt.Page[constants.PageLimitOption])))),
		Sort:       sortFields,
		Filter:     filters,
		Projection: proj,
	}

	logging.Logger.Debug("final params", "params", params)
	return params
}
